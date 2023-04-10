import { XYGlyph, XYGlyphView, XYGlyphData } from "./xy_glyph";
import * as p from "../../core/properties";
import * as mixins from "../../core/property_mixins";
import * as visuals from "../../core/visuals";
import { FloatArray, ScreenArray } from "../../core/types";
import { Context2d } from "../../core/util/canvas";
export type SplineData = XYGlyphData & {
    _xt: FloatArray;
    _yt: FloatArray;
    sxt: ScreenArray;
    syt: ScreenArray;
};
export interface SplineView extends SplineData {
}
export declare class SplineView extends XYGlyphView {
    model: Spline;
    visuals: Spline.Visuals;
    protected _set_data(): void;
    protected _map_data(): void;
    protected _render(ctx: Context2d, _indices: number[], data?: SplineData): void;
}
export declare namespace Spline {
    type Attrs = p.AttrsOf<Props>;
    type Props = XYGlyph.Props & Mixins & {
        tension: p.Property<number>;
        closed: p.Property<boolean>;
    };
    type Mixins = mixins.LineScalar;
    type Visuals = XYGlyph.Visuals & {
        line: visuals.LineScalar;
    };
}
export interface Spline extends Spline.Attrs {
}
export declare class Spline extends XYGlyph {
    properties: Spline.Props;
    __view_type__: SplineView;
    constructor(attrs?: Partial<Spline.Attrs>);
}
//# sourceMappingURL=spline.d.ts.map