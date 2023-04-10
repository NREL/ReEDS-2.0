import { LineVector, FillVector, HatchVector } from "../../core/property_mixins";
import { Rect, FloatArray, ScreenArray } from "../../core/types";
import { Anchor } from "../../core/enums";
import * as visuals from "../../core/visuals";
import { SpatialIndex } from "../../core/util/spatial";
import { Context2d } from "../../core/util/canvas";
import { Glyph, GlyphView, GlyphData } from "./glyph";
import { PointGeometry, SpanGeometry, RectGeometry } from "../../core/geometry";
import { Selection } from "../selections/selection";
import * as p from "../../core/properties";
import { Corners } from "../../core/util/bbox";
import { BorderRadius } from "../common/kinds";
export type LRTBData = GlyphData & p.UniformsOf<LRTB.Mixins> & {
    _right: FloatArray;
    _bottom: FloatArray;
    _left: FloatArray;
    _top: FloatArray;
    sright: ScreenArray;
    sbottom: ScreenArray;
    sleft: ScreenArray;
    stop: ScreenArray;
    border_radius: Corners<number>;
};
export interface LRTBView extends LRTBData {
}
export declare abstract class LRTBView extends GlyphView {
    model: LRTB;
    visuals: LRTB.Visuals;
    get_anchor_point(anchor: Anchor, i: number, _spt: [number, number]): {
        x: number;
        y: number;
    } | null;
    protected _set_data(indices: number[] | null): void;
    protected abstract _lrtb(i: number): [number, number, number, number];
    protected _index_data(index: SpatialIndex): void;
    protected _render(ctx: Context2d, indices: number[], data?: LRTBData): void;
    protected _clamp_viewport(): void;
    protected _hit_rect(geometry: RectGeometry): Selection;
    protected _hit_point(geometry: PointGeometry): Selection;
    protected _hit_span(geometry: SpanGeometry): Selection;
    draw_legend_for_index(ctx: Context2d, bbox: Rect, index: number): void;
}
export declare namespace LRTB {
    type Attrs = p.AttrsOf<Props>;
    type Props = Glyph.Props & {
        border_radius: p.Property<BorderRadius>;
    } & Mixins;
    type Mixins = LineVector & FillVector & HatchVector;
    type Visuals = Glyph.Visuals & {
        line: visuals.LineVector;
        fill: visuals.FillVector;
        hatch: visuals.HatchVector;
    };
}
export interface LRTB extends LRTB.Attrs {
}
export declare abstract class LRTB extends Glyph {
    properties: LRTB.Props;
    __view_type__: LRTBView;
    constructor(attrs?: Partial<LRTB.Attrs>);
}
//# sourceMappingURL=lrtb.d.ts.map