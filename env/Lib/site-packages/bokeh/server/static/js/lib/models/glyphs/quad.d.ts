import { LRTB, LRTBView, LRTBData } from "./lrtb";
import { FloatArray, ScreenArray } from "../../core/types";
import * as p from "../../core/properties";
export type QuadData = LRTBData & {
    _right: FloatArray;
    _bottom: FloatArray;
    _left: FloatArray;
    _top: FloatArray;
    sright: ScreenArray;
    sbottom: ScreenArray;
    sleft: ScreenArray;
    stop: ScreenArray;
};
export interface QuadView extends QuadData {
}
export declare class QuadView extends LRTBView {
    model: Quad;
    visuals: Quad.Visuals;
    lazy_initialize(): Promise<void>;
    scenterxy(i: number): [number, number];
    protected _lrtb(i: number): [number, number, number, number];
}
export declare namespace Quad {
    type Attrs = p.AttrsOf<Props>;
    type Props = LRTB.Props & {
        right: p.CoordinateSpec;
        bottom: p.CoordinateSpec;
        left: p.CoordinateSpec;
        top: p.CoordinateSpec;
    };
    type Visuals = LRTB.Visuals;
}
export interface Quad extends Quad.Attrs {
}
export declare class Quad extends LRTB {
    properties: Quad.Props;
    __view_type__: QuadView;
    constructor(attrs?: Partial<Quad.Attrs>);
}
//# sourceMappingURL=quad.d.ts.map