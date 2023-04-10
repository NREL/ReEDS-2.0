import { XYGlyph, XYGlyphView, XYGlyphData } from "./xy_glyph";
import { PointGeometry, SpanGeometry, RectGeometry, PolyGeometry } from "../../core/geometry";
import { LineVector, FillVector, HatchVector } from "../../core/property_mixins";
import * as visuals from "../../core/visuals";
import { Rect, Indices, ScreenArray } from "../../core/types";
import { RadiusDimension } from "../../core/enums";
import * as p from "../../core/properties";
import { SpatialIndex } from "../../core/util/spatial";
import { Context2d } from "../../core/util/canvas";
import { Selection } from "../selections/selection";
export type CircleData = XYGlyphData & p.UniformsOf<Circle.Mixins> & {
    readonly angle: p.Uniform<number>;
    readonly size: p.Uniform<number>;
    readonly radius: p.UniformScalar<number>;
    sradius: ScreenArray;
    readonly max_size: number;
    readonly max_radius: number;
};
export interface CircleView extends CircleData {
}
export declare class CircleView extends XYGlyphView {
    model: Circle;
    visuals: Circle.Visuals;
    lazy_initialize(): Promise<void>;
    get use_radius(): boolean;
    protected _set_data(indices: number[] | null): void;
    protected _index_data(index: SpatialIndex): void;
    protected _map_data(): void;
    protected _mask_data(): Indices;
    protected _render(ctx: Context2d, indices: number[], data?: CircleData): void;
    protected _hit_point(geometry: PointGeometry): Selection;
    protected _hit_span(geometry: SpanGeometry): Selection;
    protected _hit_rect(geometry: RectGeometry): Selection;
    protected _hit_poly(geometry: PolyGeometry): Selection;
    draw_legend_for_index(ctx: Context2d, { x0, y0, x1, y1 }: Rect, index: number): void;
}
export declare namespace Circle {
    type Attrs = p.AttrsOf<Props>;
    type Props = XYGlyph.Props & {
        angle: p.AngleSpec;
        size: p.DistanceSpec;
        radius: p.NullDistanceSpec;
        radius_dimension: p.Property<RadiusDimension>;
        hit_dilation: p.Property<number>;
    } & Mixins;
    type Mixins = LineVector & FillVector & HatchVector;
    type Visuals = XYGlyph.Visuals & {
        line: visuals.LineVector;
        fill: visuals.FillVector;
        hatch: visuals.HatchVector;
    };
}
export interface Circle extends Circle.Attrs {
}
export declare class Circle extends XYGlyph {
    properties: Circle.Props;
    __view_type__: CircleView;
    constructor(attrs?: Partial<Circle.Attrs>);
}
//# sourceMappingURL=circle.d.ts.map