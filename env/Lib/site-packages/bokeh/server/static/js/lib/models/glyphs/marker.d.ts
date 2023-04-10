import { RenderOne } from "./defs";
import { XYGlyph, XYGlyphView, XYGlyphData } from "./xy_glyph";
import { PointGeometry, SpanGeometry, RectGeometry, PolyGeometry } from "../../core/geometry";
import { LineVector, FillVector, HatchVector } from "../../core/property_mixins";
import * as visuals from "../../core/visuals";
import { Rect, Indices } from "../../core/types";
import * as p from "../../core/properties";
import { Context2d } from "../../core/util/canvas";
import { Selection } from "../selections/selection";
export type MarkerData = XYGlyphData & p.UniformsOf<Marker.Mixins> & {
    readonly size: p.Uniform<number>;
    readonly angle: p.Uniform<number>;
    readonly max_size: number;
};
export interface MarkerView extends MarkerData {
}
export declare abstract class MarkerView extends XYGlyphView {
    model: Marker;
    visuals: Marker.Visuals;
    protected _render_one: RenderOne;
    protected _render(ctx: Context2d, indices: number[], data?: MarkerData): void;
    protected _mask_data(): Indices;
    protected _hit_point(geometry: PointGeometry): Selection;
    protected _hit_span(geometry: SpanGeometry): Selection;
    protected _hit_rect(geometry: RectGeometry): Selection;
    protected _hit_poly(geometry: PolyGeometry): Selection;
    _get_legend_args({ x0, x1, y0, y1 }: Rect, index: number): MarkerData;
    draw_legend_for_index(ctx: Context2d, { x0, x1, y0, y1 }: Rect, index: number): void;
}
export declare namespace Marker {
    type Attrs = p.AttrsOf<Props>;
    type Props = XYGlyph.Props & {
        size: p.DistanceSpec;
        angle: p.AngleSpec;
        hit_dilation: p.Property<number>;
    } & Mixins;
    type Mixins = LineVector & FillVector & HatchVector;
    type Visuals = XYGlyph.Visuals & {
        line: visuals.LineVector;
        fill: visuals.FillVector;
        hatch: visuals.HatchVector;
    };
}
export interface Marker extends Marker.Attrs {
}
export declare abstract class Marker extends XYGlyph {
    properties: Marker.Props;
    __view_type__: MarkerView;
    constructor(attrs?: Partial<Marker.Attrs>);
}
//# sourceMappingURL=marker.d.ts.map