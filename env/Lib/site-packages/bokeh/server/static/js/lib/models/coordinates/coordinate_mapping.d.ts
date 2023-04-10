import { Arrayable, ScreenArray, FloatArray } from "../../core/types";
import { Model } from "../../model";
import { Scale } from "../scales/scale";
import { Range } from "../ranges/range";
import { type CartesianFrame } from "../canvas/cartesian_frame";
import * as p from "../../core/properties";
export declare class CoordinateTransform {
    readonly x_scale: Scale;
    readonly y_scale: Scale;
    readonly x_source: Range;
    readonly y_source: Range;
    readonly ranges: readonly [Range, Range];
    readonly scales: readonly [Scale, Scale];
    constructor(x_scale: Scale, y_scale: Scale);
    map_to_screen(xs: Arrayable<number>, ys: Arrayable<number>): [ScreenArray, ScreenArray];
    map_from_screen(sxs: Arrayable<number>, sys: Arrayable<number>): [FloatArray, FloatArray];
}
export declare namespace CoordinateMapping {
    type Attrs = p.AttrsOf<Props>;
    type Props = Model.Props & {
        x_source: p.Property<Range>;
        y_source: p.Property<Range>;
        x_scale: p.Property<Scale>;
        y_scale: p.Property<Scale>;
        x_target: p.Property<Range>;
        y_target: p.Property<Range>;
    };
}
export interface CoordinateMapping extends CoordinateMapping.Attrs {
}
export declare class CoordinateMapping extends Model {
    properties: CoordinateMapping.Props;
    constructor(attrs?: Partial<CoordinateMapping.Attrs>);
    get x_ranges(): Map<string, Range>;
    get y_ranges(): Map<string, Range>;
    private _get_scale;
    get_transform(frame: CartesianFrame): CoordinateTransform;
}
export declare namespace CompositeScale {
    type Attrs = p.AttrsOf<Props>;
    type Props = Scale.Props & {
        source_scale: p.Property<Scale>;
        target_scale: p.Property<Scale>;
    };
}
export interface CompositeScale extends CompositeScale.Attrs {
}
export declare class CompositeScale extends Scale {
    properties: CompositeScale.Props;
    constructor(attrs?: Partial<CompositeScale.Attrs>);
    get s_compute(): (x: number) => number;
    get s_invert(): (sx: number) => number;
    compute(x: number): number;
    v_compute(xs: Arrayable<number>): ScreenArray;
    invert(sx: number): number;
    v_invert(sxs: Arrayable<number>): FloatArray;
}
//# sourceMappingURL=coordinate_mapping.d.ts.map