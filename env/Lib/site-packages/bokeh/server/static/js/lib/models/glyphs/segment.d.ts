import { PointGeometry, SpanGeometry } from "../../core/geometry";
import * as p from "../../core/properties";
import { LineVector } from "../../core/property_mixins";
import * as visuals from "../../core/visuals";
import { Rect, FloatArray, ScreenArray } from "../../core/types";
import { SpatialIndex } from "../../core/util/spatial";
import { Context2d } from "../../core/util/canvas";
import { Glyph, GlyphView, GlyphData } from "./glyph";
import { Selection } from "../selections/selection";
export type SegmentData = GlyphData & p.UniformsOf<Segment.Mixins> & {
    _x0: FloatArray;
    _y0: FloatArray;
    _x1: FloatArray;
    _y1: FloatArray;
    sx0: ScreenArray;
    sy0: ScreenArray;
    sx1: ScreenArray;
    sy1: ScreenArray;
};
export interface SegmentView extends SegmentData {
}
export declare class SegmentView extends GlyphView {
    model: Segment;
    visuals: Segment.Visuals;
    protected _project_data(): void;
    protected _index_data(index: SpatialIndex): void;
    protected _render(ctx: Context2d, indices: number[], data?: SegmentData): void;
    protected _render_decorations(ctx: Context2d, i: number, sx0: number, sy0: number, sx1: number, sy1: number): void;
    protected _hit_point(geometry: PointGeometry): Selection;
    protected _hit_span(geometry: SpanGeometry): Selection;
    scenterxy(i: number): [number, number];
    draw_legend_for_index(ctx: Context2d, bbox: Rect, index: number): void;
}
export declare namespace Segment {
    type Attrs = p.AttrsOf<Props>;
    type Props = Glyph.Props & {
        x0: p.CoordinateSpec;
        y0: p.CoordinateSpec;
        x1: p.CoordinateSpec;
        y1: p.CoordinateSpec;
    } & Mixins;
    type Mixins = LineVector;
    type Visuals = Glyph.Visuals & {
        line: visuals.LineVector;
    };
}
export interface Segment extends Segment.Attrs {
}
export declare class Segment extends Glyph {
    properties: Segment.Props;
    __view_type__: SegmentView;
    constructor(attrs?: Partial<Segment.Attrs>);
}
//# sourceMappingURL=segment.d.ts.map