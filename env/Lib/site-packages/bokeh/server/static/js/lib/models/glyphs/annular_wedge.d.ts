import { XYGlyph, XYGlyphView, XYGlyphData } from "./xy_glyph";
import { PointGeometry } from "../../core/geometry";
import { LineVector, FillVector, HatchVector } from "../../core/property_mixins";
import { Rect, ScreenArray } from "../../core/types";
import * as visuals from "../../core/visuals";
import { Direction } from "../../core/enums";
import * as p from "../../core/properties";
import { Context2d } from "../../core/util/canvas";
import { Selection } from "../selections/selection";
export type AnnularWedgeData = XYGlyphData & p.UniformsOf<AnnularWedge.Mixins> & {
    readonly inner_radius: p.Uniform<number>;
    readonly outer_radius: p.Uniform<number>;
    readonly start_angle: p.Uniform<number>;
    readonly end_angle: p.Uniform<number>;
    sinner_radius: ScreenArray;
    souter_radius: ScreenArray;
    max_souter_radius: number;
    readonly max_inner_radius: number;
    readonly max_outer_radius: number;
};
export interface AnnularWedgeView extends AnnularWedgeData {
}
export declare class AnnularWedgeView extends XYGlyphView {
    model: AnnularWedge;
    visuals: AnnularWedge.Visuals;
    protected _map_data(): void;
    protected _render(ctx: Context2d, indices: number[], data?: AnnularWedgeData): void;
    protected _hit_point(geometry: PointGeometry): Selection;
    draw_legend_for_index(ctx: Context2d, bbox: Rect, index: number): void;
    scenterxy(i: number): [number, number];
}
export declare namespace AnnularWedge {
    type Attrs = p.AttrsOf<Props>;
    type Props = XYGlyph.Props & {
        direction: p.Property<Direction>;
        inner_radius: p.DistanceSpec;
        outer_radius: p.DistanceSpec;
        start_angle: p.AngleSpec;
        end_angle: p.AngleSpec;
    } & Mixins;
    type Mixins = LineVector & FillVector & HatchVector;
    type Visuals = XYGlyph.Visuals & {
        line: visuals.LineVector;
        fill: visuals.FillVector;
        hatch: visuals.HatchVector;
    };
}
export interface AnnularWedge extends AnnularWedge.Attrs {
}
export declare class AnnularWedge extends XYGlyph {
    properties: AnnularWedge.Props;
    __view_type__: AnnularWedgeView;
    constructor(attrs?: Partial<AnnularWedge.Attrs>);
}
//# sourceMappingURL=annular_wedge.d.ts.map