# pyrefly: ignore [missing-import]
from nicegui import ui
from typing import Callable, Optional, Dict, Any
import math
from services.benchmark_service import benchmark_service
import config
from i18n import t, ds_text

OWN_ORG = "VAGO Solutions"
# colour = maximum context length (sequential): one hue (VAGO violet), dark -> light on a dark background
TOKEN_RAMP = ["#4a2fa6", "#6a46e6", "#8f74ff", "#b7a6ff", "#e4dcff"]


class ModelSizeChart:
    def __init__(self, lang: str, on_model_click: Optional[Callable] = None):
        self.lang = lang
        self.on_model_click = on_model_click
        self.current_dataset = "overall"
        self.chart_container = None
        self.echart_element = None

    def render(self):
        L = self.lang
        with ui.element("div").classes("w-full max-w-7xl mx-auto px-4 pb-12"):
            with ui.element("div").classes("ci-card w-full p-5 md:p-8"):
                with ui.row().classes("w-full justify-between items-start flex-wrap gap-4 mb-4"):
                    with ui.column().classes("gap-1 flex-1 min-w-[260px]"):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("scatter_plot", size="sm").classes("ci-yellow")
                            ui.label(t(L, "chart.title")).classes("ci-title text-lg md:text-xl")
                        ui.label(t(L, "chart.lead")).classes("text-xs md:text-sm ci-muted leading-relaxed")
                    with ui.row().classes("items-center gap-2"):
                        ui.label(t(L, "chart.dataset")).classes("ci-kicker")
                        ui.select(options={k: (ds_text(L, k, "short") if k != "overall" else "Overall") for k in config.DATASETS_INFO},
                                  value="overall", on_change=self._on_dataset_change).props(
                            "outlined dense dark options-dense").classes("w-52 text-xs").bind_value(self, "current_dataset")

                with ui.row().classes("items-center gap-2 mb-5 flex-wrap text-xs"):
                    for icon, key in (("horizontal_rule", "chart.x"), ("vertical_align_top", "chart.y"),
                                      ("lens", "chart.bubble"), ("palette", "chart.color")):
                        with ui.row().classes("items-center gap-1.5 px-3 py-1 ci-subcard"):
                            ui.icon(icon, size="xs").classes("ci-yellow")
                            ui.label(t(L, key)).classes("ci-text font-medium")
                    with ui.row().classes("items-center gap-1.5 px-3 py-1 ci-subcard"):
                        ui.element("span").classes("ci-drop-dot")
                        ui.label(t(L, "chart.own")).classes("ci-text font-medium")

                self.chart_container = ui.column().classes("w-full")
                self.refresh_chart()

    def _on_dataset_change(self):
        self.refresh_chart()

    def _get_echart_options(self) -> Dict[str, Any]:
        L = self.lang
        scatter_data = benchmark_service.get_scatter_plot_data(self.current_dataset)
        points = []
        for p in scatter_data:
            own = p["organization"] == OWN_ORG
            points.append({
                "value": [p["parameters"], p["score"], p["dimension"], p["max_tokens"], p["model_name"], p["organization"],
                          p["model_type"], p["embedding_type"], p["id"]],
                "itemStyle": {"borderColor": "#F8D84A" if own else "rgba(255,255,255,0.75)", "borderWidth": 3 if own else 1},
            })
        scores = [p["score"] for p in scatter_data] or [0.5]
        y_min = max(0.0, math.floor((min(scores) - 0.03) * 20) / 20)
        y_max = min(1.0, math.ceil((max(scores) + 0.03) * 20) / 20)
        name = "Overall" if self.current_dataset == "overall" else ds_text(L, self.current_dataset, "name")
        def js(key):  # escape a text for a single-quoted JS string
            return t(L, key).replace("\\", "\\\\").replace("'", "\\'").replace("<", "&lt;")
        click_hint = js("chart.tip_click")
        tip_score, tip_params, tip_dim, tip_ctx, lexical = (js("chart.tip_score"), js("chart.tip_params"),
                                                             js("chart.tip_dim"), js("chart.tip_ctx"), js("chart.tip_lexical"))
        return {
            "backgroundColor": "transparent",
            "textStyle": {"fontFamily": "Inter, system-ui, sans-serif"},
            "title": {"text": name, "left": "16px", "top": "6px", "textStyle": {"color": "#FFFFFF", "fontSize": 14, "fontWeight": 700}},
            "grid": {"left": "56px", "right": "110px", "top": "48px", "bottom": "60px", "containLabel": True},
            "tooltip": {
                "trigger": "item", "backgroundColor": "#0a0614", "borderColor": "rgba(128, 84, 255, 0.6)", "borderWidth": 1.5,
                "padding": 12, "textStyle": {"color": "#FFFFFF"},
                "extraCssText": "box-shadow: 0 12px 32px rgba(0,0,0,0.8); border-radius: 14px 7px 0 7px;",
                ":formatter": """
                function(params) {
                    var d = params.data.value;
                    var v = d[0], f = '';
                    if (v === 1) f = '1 (BM25)';
                    else if (v >= 1e9) f = (v / 1e9).toFixed(2).replace(/\\.?0+$/, '') + 'B';
                    else if (v >= 1e6) f = (v / 1e6).toFixed(1).replace(/\\.?0+$/, '') + 'M';
                    else f = v.toString();
                    return '<div style="min-width: 220px;">' +
                        '<div style="font-weight: 800; font-size: 14px; color: #F8D84A; margin-bottom: 2px;">' + d[4] + '</div>' +
                        '<div style="font-size: 11px; color: #c5b4ff; font-weight: 600; margin-bottom: 8px;">' + d[5] + ' · ' + d[7] + '</div>' +
                        '<div style="border-top: 1px solid rgba(255,255,255,0.12); padding-top: 6px; display: flex; flex-direction: column; gap: 4px; font-size: 12px;">' +
                        '<div style="display:flex; justify-content:space-between; gap:12px;"><span style="color:#a49db9;">""" + tip_score + """</span><strong>' + d[1].toFixed(4) + '</strong></div>' +
                        '<div style="display:flex; justify-content:space-between; gap:12px;"><span style="color:#a49db9;">""" + tip_params + """</span><strong>' + f + '</strong></div>' +
                        '<div style="display:flex; justify-content:space-between; gap:12px;"><span style="color:#a49db9;">""" + tip_dim + """</span><strong>' + (d[2] > 0 ? d[2] + 'd' : '""" + lexical + """') + '</strong></div>' +
                        '<div style="display:flex; justify-content:space-between; gap:12px;"><span style="color:#a49db9;">""" + tip_ctx + """</span><strong>' + d[3].toLocaleString('""" + ("de-DE" if L == "de" else "en-US") + """') + ' tok</strong></div>' +
                        '</div><div style="margin-top: 8px; font-size: 10px; color: #756e8d; text-align: right;">""" + click_hint + """</div></div>';
                }
                """,
            },
            "xAxis": {
                "type": "log", "logBase": 10, "min": 1_000_000, "max": 15_000_000_000,
                "name": t(L, "chart.x_axis"), "nameLocation": "middle", "nameGap": 34,
                "nameTextStyle": {"color": "#a49db9", "fontSize": 12, "fontWeight": 600},
                "axisLine": {"lineStyle": {"color": "#3a3150"}}, "axisTick": {"lineStyle": {"color": "#3a3150"}},
                "axisLabel": {"color": "#a49db9", "fontSize": 11, ":formatter": """
                    function(value) {
                        if (value >= 1e9) return (value/1e9) + 'B';
                        if (value >= 1e6) return (value/1e6) + 'M';
                        if (value >= 1e3) return (value/1e3) + 'k';
                        return value;
                    }"""},
                "splitLine": {"show": True, "lineStyle": {"color": "rgba(255,255,255,0.05)", "type": "dashed"}},
            },
            "yAxis": {
                "type": "value", "name": t(L, "chart.y_axis"), "nameLocation": "middle", "nameGap": 44,
                "nameTextStyle": {"color": "#a49db9", "fontSize": 12, "fontWeight": 600},
                "min": y_min, "max": y_max,
                "axisLine": {"lineStyle": {"color": "#3a3150"}}, "axisTick": {"lineStyle": {"color": "#3a3150"}},
                "axisLabel": {"color": "#a49db9", "fontSize": 11, ":formatter": "function(value) { return value.toFixed(2); }"},
                "splitLine": {"show": True, "lineStyle": {"color": "rgba(255,255,255,0.06)"}},
            },
            "visualMap": [{
                "show": True, "dimension": 3, "min": 512, "max": 65536, "text": [t(L, "chart.vm_high"), "512"],
                "textGap": 10, "itemWidth": 12, "itemHeight": 160, "calculable": False, "orient": "vertical",
                "right": "12px", "top": "center", "inRange": {"color": TOKEN_RAMP},
                "textStyle": {"color": "#a49db9", "fontSize": 10, "fontWeight": "bold"},
            }],
            "series": [{
                "name": "models", "type": "scatter", "data": points,
                ":symbolSize": """
                function(data) {
                    var dim = data[2] || 768;
                    if (dim <= 0) dim = 128;
                    return Math.max(14, Math.min(48, Math.sqrt(dim) * 0.65 + 8));
                }""",
                "itemStyle": {"opacity": 0.92},
                "emphasis": {"focus": "self", "itemStyle": {"borderColor": "#F8D84A", "borderWidth": 3, "opacity": 1.0}},
                "label": {"show": False},
            }],
        }

    def refresh_chart(self):
        if not self.chart_container:
            return
        self.chart_container.clear()
        with self.chart_container:
            self.echart_element = ui.echart(self._get_echart_options()).classes("w-full h-[520px]")
            if self.on_model_click:
                self.echart_element.on("click", self._handle_chart_click)

    def _handle_chart_click(self, event):
        try:
            data = event.args.get("data") if isinstance(event.args, dict) else None
            arr = data.get("value") if isinstance(data, dict) else data
            if arr and len(arr) >= 9:
                item = benchmark_service.get_model_item(arr[8], self.current_dataset)
                if item and self.on_model_click:
                    self.on_model_click(item)
        except Exception as e:
            print(f"Error handling chart click: {e}")
