"""Тесты графики: SVG-примитивы, страница отчёта, сцены шапок."""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.viz import header, report
from tools.viz import svg as art


class PrimitivesTest(unittest.TestCase):
    def test_escape(self):
        self.assertEqual(art.esc("<b>&"), "&lt;b&gt;&amp;")

    def test_number_format(self):
        self.assertEqual(art.num(1.23456), "1.2")

    def test_rect_has_size(self):
        self.assertIn('width="30.0"', art.rect(0, 0, 30, 40, "#fff"))

    def test_negative_size_clamped(self):
        self.assertIn('width="0.0"', art.rect(0, 0, -5, 40, "#fff"))

    def test_text_anchor(self):
        self.assertIn('text-anchor="end"', art.text(0, 0, "x", anchor="end"))

    def test_line_dash(self):
        self.assertIn("stroke-dasharray", art.line(0, 0, 1, 1, "#000", dash="4 6"))

    def test_polyline_points(self):
        self.assertIn("0.0,0.0 10.0,10.0", art.polyline([(0, 0), (10, 10)], "#000"))

    def test_circle_radius(self):
        self.assertIn('r="4.5"', art.circle(1, 2, 4.5, "#000"))

    def test_svg_root(self):
        self.assertTrue(art.svg(100, 50, "", "t").startswith("<svg"))

    def test_svg_animated_flag(self):
        self.assertIn("animated", art.svg(10, 10, "", "t", animated=True))

    def test_norm_maps_range(self):
        self.assertEqual(art.norm(5, 0, 10, 0, 100), 50)

    def test_norm_zero_span(self):
        self.assertEqual(art.norm(5, 5, 5, 0, 100), 0)

    def test_mix_middle(self):
        self.assertEqual(art.mix("#000000", "#ffffff", 0.5), "#808080")


class ChartsTest(unittest.TestCase):
    def test_bar_chart_has_bars(self):
        chart = art.bar_chart(["a", "b"], [{"name": "n", "values": [1, 2]}], title="t")
        self.assertGreaterEqual(chart.count("<rect"), 3)

    def test_bar_chart_custom_color(self):
        chart = art.bar_chart(["a"], [{"name": "n", "values": [1], "color": "#123456"}])
        self.assertIn("#123456", chart)

    def test_bar_chart_empty(self):
        self.assertIn("<svg", art.bar_chart([], []))

    def test_line_chart_points(self):
        chart = art.line_chart(["a", "b"], [{"name": "n", "values": [1, 3]}], title="t")
        self.assertIn("<polyline", chart)

    def test_line_chart_without_dots(self):
        chart = art.line_chart(["a"], [{"name": "n", "values": [1]}], dots=False)
        self.assertNotIn("<circle", chart)

    def test_scatter_groups(self):
        points = [{"x": 1, "y": 2, "group": "g1"}, {"x": 3, "y": 4, "group": "g2"}]
        self.assertIn("g1", art.scatter(points, title="t"))

    def test_scatter_single_group(self):
        points = [{"x": 1, "y": 2, "group": "g1"}]
        self.assertIn("<circle", art.scatter(points))

    def test_heatmap_cells(self):
        heat = art.heatmap(["r1", "r2"], ["c1"], [[0.0], [1.0]], title="t")
        self.assertGreaterEqual(heat.count("<rect"), 3)

    def test_dag_boxes_and_arrows(self):
        chart = art.dag([{"label": "a", "sub": "1"}, {"label": "b", "sub": "2"}], ["x"])
        self.assertIn("<line", chart)

    def test_dag_single_node(self):
        self.assertIn("<svg", art.dag([{"label": "a"}], []))

    def test_tiles_map_labels(self):
        tiles = [{"label": "ЦФО", "x": 0, "y": 0, "w": 0.2, "h": 0.2, "value": 0.5}]
        self.assertIn("ЦФО", art.tiles_map(tiles, title="t"))

    def test_table_rows(self):
        html = art.table(["h"], [["v"]], flags=["ok"], caption="c")
        self.assertIn('class="ok"', html)

    def test_table_without_flags(self):
        self.assertIn("<td>v</td>", art.table(["h"], [["v"]]))

    def test_terminal_block(self):
        self.assertIn("terminal", art.terminal(["$ ls"], "t"))

    def test_stat_cards_tone(self):
        self.assertIn("card ok", art.stat_cards([{"value": "1", "label": "l", "tone": "ok"}]))

    def test_kanban_columns(self):
        board = art.kanban([{"title": "Открыто", "cards": [{"title": "t", "tag": "g"}]}])
        self.assertIn("Открыто", board)


class ReportPageTest(unittest.TestCase):
    def test_page_structure(self):
        html = report.page("Заголовок", "Подзаголовок", [report.section("01", "С", "н", "<b>x</b>")], footer="f", badges=["b"])
        self.assertIn("<!doctype html", html)

    def test_page_without_footer(self):
        html = report.page("T", "S", [])
        self.assertNotIn("<footer>", html)

    def test_section_id(self):
        self.assertIn('id="s01"', report.section("01", "С", "н", ""))

    def test_figure_caption(self):
        self.assertIn("cap", report.figure("cap", "<svg></svg>"))

    def test_write_creates_file(self):
        target = Path(tempfile.mkdtemp()) / "deep" / "page.html"
        self.assertTrue(Path(report.write(target, "<p>x</p>")).exists())

    def test_write_uses_lf(self):
        target = Path(report.write(Path(tempfile.mkdtemp()) / "p.html", "a\nb"))
        self.assertNotIn(b"\r\n", target.read_bytes())


class HeaderTest(unittest.TestCase):
    def test_seven_scenes(self):
        self.assertEqual(len(header.SCENES), 7)

    def test_every_scene_has_animation(self):
        self.assertTrue(all("<animate" in painter() for _, painter in header.SCENES))

    def test_every_scene_has_title(self):
        self.assertTrue(all("Проект" in painter() for _, painter in header.SCENES))

    def test_render_wraps_svg(self):
        self.assertTrue(header.render(header.SCENES[0]).startswith("<svg"))

    def test_fade_box_starts_hidden(self):
        self.assertIn('opacity="0"', header.fade_box(0, 0, 10, 10, "#fff", 0.5))

    def test_grow_bar_animates_height(self):
        self.assertIn("attributeName=\"height\"", header.grow_bar(0, 100, 10, 50, "#fff", 0))

    def test_slide_dot_animates_position(self):
        self.assertIn("attributeName=\"cx\"", header.slide_dot(10, 10, 4, "#fff", 0))

    def test_main_writes_files(self):
        self.assertEqual(header.main([]), 0)


if __name__ == "__main__":
    unittest.main()
