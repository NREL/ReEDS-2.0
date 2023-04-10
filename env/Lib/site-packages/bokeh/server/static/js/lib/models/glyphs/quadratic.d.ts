import { LineVector } from "../../core/property_mixins";
import * as visuals from "../../core/visuals";
import { Rect, FloatArray, ScreenArray } from "../../core/types";
import { SpatialIndex } from "../../core/util/spatial";
import { Context2d } from "../../core/util/canvas";
import { Glyph, GlyphView, GlyphData } from "./glyph";
import * as p from "../../core/properties";
export type QuadraticData = GlyphData & p.UniformsOf<Quadratic.Mixins> & {
    _x0: FloatArray;
    _y0: FloatArray;
    _x1: FloatArray;
    _y1: FloatArray;
    _cx: FloatArray;
    _cy: FloatArray;
    sx0: ScreenArray;
    sy0: ScreenArray;
    sx1: ScreenArray;
    sy1: ScreenArray;
    scx: ScreenArray;
    scy: ScreenArray;
};
export interface QuadraticView extends QuadraticData {
}
export declare class QuadraticView extends GlyphView {
    model: Quadratic;
    visuals: Quadratic.Visuals;
    protected _project_data(): void;
    protected _index_data(index: SpatialIndex): void;
    protected _render(ctx: Context2d, indices: number[], data?: QuadraticData): void;
    draw_legend_for_index(ctx: Context2d, bbox: Rect, index: number): void;
    scenterxy(): [number, number];
}
export declare namespace Quadratic {
    type Attrs = p.AttrsOf<Props>;
    type Props = Glyph.Props & {
        x0: p.CoordinateSpec;
        y0: p.CoordinateSpec;
        x1: p.CoordinateSpec;
        y1: p.CoordinateSpec;
        cx: p.CoordinateSpec;
        cy: p.CoordinateSpec;
    } & Mixins;
    type Mixins = LineVector;
    type Visuals = Glyph.Visuals & {
        line: visuals.LineVector;
    };
}
export interface Quadratic extends Quadratic.Attrs {
}
export declare class Quadratic extends Glyph {
    properties: Quadratic.Props;
    __view_type__: QuadraticView;
    constructor(attrs?: Partial<Quadratic.Attrs>);
}
//# sourceMappingURL=quadratic.d.ts.map