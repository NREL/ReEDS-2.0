import { XYGlyph, XYGlyphView, XYGlyphData } from "./xy_glyph";
import { Rect, ScreenArray } from "../../core/types";
import { PointGeometry } from "../../core/geometry";
import { LineVector, FillVector, HatchVector } from "../../core/property_mixins";
import * as visuals from "../../core/visuals";
import * as p from "../../core/properties";
import { Context2d } from "../../core/util/canvas";
import { Selection } from "../selections/selection";
export type AnnulusData = XYGlyphData & p.UniformsOf<Annulus.Mixins> & {
    readonly inner_radius: p.Uniform<number>;
    readonly outer_radius: p.Uniform<number>;
    sinner_radius: ScreenArray;
    souter_radius: ScreenArray;
    readonly max_inner_radius: number;
    readonly max_outer_radius: number;
};
export interface AnnulusView extends AnnulusData {
}
export declare class AnnulusView extends XYGlyphView {
    model: Annulus;
    visuals: Annulus.Visuals;
    protected _map_data(): void;
    protected _render(ctx: Context2d, indices: number[], data?: AnnulusData): void;
    protected _hit_point(geometry: PointGeometry): Selection;
    draw_legend_for_index(ctx: Context2d, { x0, y0, x1, y1 }: Rect, index: number): void;
}
export declare namespace Annulus {
    type Attrs = p.AttrsOf<Props>;
    type Props = XYGlyph.Props & {
        inner_radius: p.DistanceSpec;
        outer_radius: p.DistanceSpec;
    } & Mixins;
    type Mixins = LineVector & FillVector & HatchVector;
    type Visuals = XYGlyph.Visuals & {
        line: visuals.LineVector;
        fill: visuals.FillVector;
        hatch: visuals.HatchVector;
    };
}
export interface Annulus extends Annulus.Attrs {
}
export declare class Annulus extends XYGlyph {
    properties: Annulus.Props;
    __view_type__: AnnulusView;
    constructor(attrs?: Partial<Annulus.Attrs>);
}
//# sourceMappingURL=annulus.d.ts.map