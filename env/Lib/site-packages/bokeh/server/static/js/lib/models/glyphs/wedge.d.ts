import { XYGlyph, XYGlyphView, XYGlyphData } from "./xy_glyph";
import { PointGeometry } from "../../core/geometry";
import { LineVector, FillVector, HatchVector } from "../../core/property_mixins";
import * as visuals from "../../core/visuals";
import { Rect, ScreenArray } from "../../core/types";
import { Direction } from "../../core/enums";
import * as p from "../../core/properties";
import { Context2d } from "../../core/util/canvas";
import { Selection } from "../selections/selection";
export type WedgeData = XYGlyphData & p.UniformsOf<Wedge.Mixins> & {
    readonly radius: p.Uniform<number>;
    sradius: ScreenArray;
    max_sradius: number;
    readonly max_radius: number;
    readonly start_angle: p.Uniform<number>;
    readonly end_angle: p.Uniform<number>;
};
export interface WedgeView extends WedgeData {
}
export declare class WedgeView extends XYGlyphView {
    model: Wedge;
    visuals: Wedge.Visuals;
    protected _map_data(): void;
    protected _render(ctx: Context2d, indices: number[], data?: WedgeData): void;
    protected _hit_point(geometry: PointGeometry): Selection;
    draw_legend_for_index(ctx: Context2d, bbox: Rect, index: number): void;
    scenterxy(i: number): [number, number];
}
export declare namespace Wedge {
    type Attrs = p.AttrsOf<Props>;
    type Props = XYGlyph.Props & {
        direction: p.Property<Direction>;
        radius: p.DistanceSpec;
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
export interface Wedge extends Wedge.Attrs {
}
export declare class Wedge extends XYGlyph {
    properties: Wedge.Props;
    __view_type__: WedgeView;
    constructor(attrs?: Partial<Wedge.Attrs>);
}
//# sourceMappingURL=wedge.d.ts.map