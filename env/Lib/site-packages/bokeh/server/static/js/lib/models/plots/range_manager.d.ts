import { Range } from "../ranges/range";
import { CartesianFrame } from "../canvas/cartesian_frame";
import { CoordinateMapping } from "../coordinates/coordinate_mapping";
import type { PlotView } from "./plot_canvas";
import { Interval } from "../../core/types";
export type RangeInfo = {
    xrs: Map<string, Interval>;
    yrs: Map<string, Interval>;
};
export type RangeOptions = {
    panning?: boolean;
    scrolling?: boolean;
    maintain_focus?: boolean;
};
export declare class RangeManager {
    readonly parent: PlotView;
    constructor(parent: PlotView);
    get frame(): CartesianFrame;
    invalidate_dataranges: boolean;
    update(range_info: RangeInfo | null, options?: RangeOptions): void;
    reset(): void;
    protected _update_dataranges(frame: CartesianFrame | CoordinateMapping): void;
    update_dataranges(): void;
    compute_initial(): RangeInfo | null;
    protected _update_ranges_together(range_info_iter: [Range, Interval][]): void;
    protected _update_ranges_individually(range_info_iter: [Range, Interval][], options?: RangeOptions): void;
    protected _get_weight_to_constrain_interval(rng: Range, range_info: Interval): number;
}
//# sourceMappingURL=range_manager.d.ts.map