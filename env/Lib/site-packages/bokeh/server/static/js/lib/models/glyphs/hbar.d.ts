import { LRTB, LRTBView, LRTBData } from "./lrtb";
import { FloatArray, ScreenArray } from "../../core/types";
import * as p from "../../core/properties";
export type HBarData = LRTBData & {
    _left: FloatArray;
    _y: FloatArray;
    readonly height: p.Uniform<number>;
    _right: FloatArray;
    sy: ScreenArray;
    sh: ScreenArray;
    sleft: ScreenArray;
    sright: ScreenArray;
    stop: ScreenArray;
    sbottom: ScreenArray;
};
export interface HBarView extends HBarData {
}
export declare class HBarView extends LRTBView {
    model: HBar;
    visuals: HBar.Visuals;
    lazy_initialize(): Promise<void>;
    scenterxy(i: number): [number, number];
    protected _lrtb(i: number): [number, number, number, number];
    protected _map_data(): void;
}
export declare namespace HBar {
    type Attrs = p.AttrsOf<Props>;
    type Props = LRTB.Props & {
        left: p.CoordinateSpec;
        y: p.CoordinateSpec;
        height: p.NumberSpec;
        right: p.CoordinateSpec;
    };
    type Visuals = LRTB.Visuals;
}
export interface HBar extends HBar.Attrs {
}
export declare class HBar extends LRTB {
    properties: HBar.Props;
    __view_type__: HBarView;
    constructor(attrs?: Partial<HBar.Attrs>);
}
//# sourceMappingURL=hbar.d.ts.map