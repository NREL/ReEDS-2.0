import * as mixins from "../../core/property_mixins";
import * as visuals from "../../core/visuals";
import * as p from "../../core/properties";
import { Signal0 } from "../../core/signaling";
import { Location, OutputBackend, Place, ResetPolicy } from "../../core/enums";
import { LRTB } from "../../core/util/bbox";
import { LayoutDOM } from "../layouts/layout_dom";
import { Axis } from "../axes/axis";
import { Grid } from "../grids/grid";
import { GuideRenderer } from "../renderers/guide_renderer";
import { Annotation } from "../annotations/annotation";
import { Title } from "../annotations/title";
import { Toolbar } from "../tools/toolbar";
import { Range } from "../ranges/range";
import { Scale } from "../scales/scale";
import { Glyph } from "../glyphs/glyph";
import { ColumnarDataSource } from "../sources/columnar_data_source";
import { Renderer } from "../renderers/renderer";
import { DataRenderer } from "../renderers/data_renderer";
import { GlyphRenderer } from "../renderers/glyph_renderer";
import { Tool, ToolAliases } from "../tools/tool";
import { PlotView } from "./plot_canvas";
export { PlotView };
export declare namespace Plot {
    type Attrs = p.AttrsOf<Props>;
    type Props = LayoutDOM.Props & {
        toolbar: p.Property<Toolbar>;
        toolbar_location: p.Property<Location | null>;
        toolbar_sticky: p.Property<boolean>;
        toolbar_inner: p.Property<boolean>;
        frame_width: p.Property<number | null>;
        frame_height: p.Property<number | null>;
        frame_align: p.Property<boolean | Partial<LRTB<boolean>>>;
        title: p.Property<Title | string | null>;
        title_location: p.Property<Location | null>;
        above: p.Property<(Annotation | Axis)[]>;
        below: p.Property<(Annotation | Axis)[]>;
        left: p.Property<(Annotation | Axis)[]>;
        right: p.Property<(Annotation | Axis)[]>;
        center: p.Property<(Annotation | Grid)[]>;
        renderers: p.Property<Renderer[]>;
        x_range: p.Property<Range>;
        y_range: p.Property<Range>;
        x_scale: p.Property<Scale>;
        y_scale: p.Property<Scale>;
        extra_x_ranges: p.Property<{
            [key: string]: Range;
        }>;
        extra_y_ranges: p.Property<{
            [key: string]: Range;
        }>;
        extra_x_scales: p.Property<{
            [key: string]: Scale;
        }>;
        extra_y_scales: p.Property<{
            [key: string]: Scale;
        }>;
        lod_factor: p.Property<number>;
        lod_interval: p.Property<number>;
        lod_threshold: p.Property<number | null>;
        lod_timeout: p.Property<number>;
        hidpi: p.Property<boolean>;
        output_backend: p.Property<OutputBackend>;
        min_border: p.Property<number | null>;
        min_border_top: p.Property<number | null>;
        min_border_left: p.Property<number | null>;
        min_border_bottom: p.Property<number | null>;
        min_border_right: p.Property<number | null>;
        inner_width: p.Property<number>;
        inner_height: p.Property<number>;
        outer_width: p.Property<number>;
        outer_height: p.Property<number>;
        match_aspect: p.Property<boolean>;
        aspect_scale: p.Property<number>;
        reset_policy: p.Property<ResetPolicy>;
        hold_render: p.Property<boolean>;
    } & Mixins;
    type Mixins = mixins.OutlineLine & mixins.BackgroundFill & mixins.BorderFill;
    type Visuals = visuals.Visuals & {
        outline_line: visuals.Line;
        background_fill: visuals.Fill;
        border_fill: visuals.Fill;
    };
}
export interface Plot extends Plot.Attrs {
}
export declare class Plot extends LayoutDOM {
    properties: Plot.Props;
    __view_type__: PlotView;
    readonly use_map: boolean;
    readonly reset: Signal0<this>;
    constructor(attrs?: Partial<Plot.Attrs>);
    add_layout(renderer: Annotation | GuideRenderer, side?: Place): void;
    remove_layout(renderer: Annotation | GuideRenderer): void;
    get data_renderers(): DataRenderer[];
    add_renderers(...renderers: Renderer[]): void;
    add_glyph(glyph: Glyph, source?: ColumnarDataSource, attrs?: Partial<GlyphRenderer.Attrs>): GlyphRenderer;
    add_tools(...tools: (Tool | keyof ToolAliases)[]): void;
    remove_tools(...tools: Tool[]): void;
    get panels(): (Annotation | Axis | Grid)[];
    get side_panels(): (Annotation | Axis)[];
}
//# sourceMappingURL=plot.d.ts.map