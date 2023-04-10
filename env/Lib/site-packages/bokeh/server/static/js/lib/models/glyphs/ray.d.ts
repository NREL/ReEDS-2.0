import { XYGlyph, XYGlyphView, XYGlyphData } from "./xy_glyph";
import { LineVector } from "../../core/property_mixins";
import * as visuals from "../../core/visuals";
import { Rect, ScreenArray } from "../../core/types";
import * as p from "../../core/properties";
import { Context2d } from "../../core/util/canvas";
export type RayData = XYGlyphData & p.UniformsOf<Ray.Mixins> & {
    readonly length: p.Uniform<number>;
    readonly angle: p.Uniform<number>;
    slength: ScreenArray;
};
export interface RayView extends RayData {
}
export declare class RayView extends XYGlyphView {
    model: Ray;
    visuals: Ray.Visuals;
    protected _map_data(): void;
    protected _render(ctx: Context2d, indices: number[], data?: RayData): void;
    draw_legend_for_index(ctx: Context2d, bbox: Rect, index: number): void;
}
export declare namespace Ray {
    type Attrs = p.AttrsOf<Props>;
    type Props = XYGlyph.Props & {
        length: p.DistanceSpec;
        angle: p.AngleSpec;
    } & Mixins;
    type Mixins = LineVector;
    type Visuals = XYGlyph.Visuals & {
        line: visuals.LineVector;
    };
}
export interface Ray extends Ray.Attrs {
}
export declare class Ray extends XYGlyph {
    properties: Ray.Props;
    __view_type__: RayView;
    constructor(attrs?: Partial<Ray.Attrs>);
}
//# sourceMappingURL=ray.d.ts.map