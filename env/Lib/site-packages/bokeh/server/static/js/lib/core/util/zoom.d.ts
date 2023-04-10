import { Interval } from "../types";
import { CartesianFrame } from "../../models/canvas/cartesian_frame";
import { Scale } from "../../models/scales/scale";
export declare function scale_highlow(range: Interval, factor: number, center?: number): [number, number];
export declare function get_info(scales: Map<string, Scale>, [sxy0, sxy1]: [number, number]): Map<string, Interval>;
export type ScaleRange = {
    xrs: Map<string, Interval>;
    yrs: Map<string, Interval>;
    factor: number;
};
export declare function scale_range(frame: CartesianFrame, factor: number, h_axis?: boolean, v_axis?: boolean, center?: {
    x: number;
    y: number;
}): ScaleRange;
//# sourceMappingURL=zoom.d.ts.map