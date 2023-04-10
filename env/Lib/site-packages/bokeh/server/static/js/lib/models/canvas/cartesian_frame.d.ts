import { Scale } from "../scales/scale";
import { Range } from "../ranges/range";
import { Range1d } from "../ranges/range1d";
import { BBox } from "../../core/util/bbox";
import { Signal0 } from "../../core/signaling";
type Ranges = {
    [key: string]: Range;
};
type Scales = {
    [key: string]: Scale;
};
export declare class CartesianFrame {
    in_x_scale: Scale;
    in_y_scale: Scale;
    x_range: Range;
    y_range: Range;
    extra_x_ranges: Ranges;
    extra_y_ranges: Ranges;
    extra_x_scales: Scales;
    extra_y_scales: Scales;
    private _bbox;
    get bbox(): BBox;
    readonly change: Signal0<this>;
    constructor(in_x_scale: Scale, in_y_scale: Scale, x_range: Range, y_range: Range, extra_x_ranges?: Ranges, extra_y_ranges?: Ranges, extra_x_scales?: Scales, extra_y_scales?: Scales);
    protected _x_target: Range1d;
    protected _y_target: Range1d;
    protected _x_ranges: Map<string, Range>;
    protected _y_ranges: Map<string, Range>;
    protected _x_scales: Map<string, Scale>;
    protected _y_scales: Map<string, Scale>;
    protected _get_ranges(range: Range, extra_ranges: Ranges): Map<string, Range>;
    _get_scales(scale: Scale, extra_scales: Scales, ranges: Map<string, Range>, frame_range: Range): Map<string, Scale>;
    protected _configure_frame_ranges(): void;
    protected _configure_scales(): void;
    configure_scales(): void;
    protected _update_scales(): void;
    set_geometry(bbox: BBox): void;
    get x_target(): Range1d;
    get y_target(): Range1d;
    get x_ranges(): Map<string, Range>;
    get y_ranges(): Map<string, Range>;
    get ranges(): Set<Range>;
    get x_scales(): Map<string, Scale>;
    get y_scales(): Map<string, Scale>;
    get scales(): Set<Scale>;
    get x_scale(): Scale;
    get y_scale(): Scale;
}
export {};
//# sourceMappingURL=cartesian_frame.d.ts.map