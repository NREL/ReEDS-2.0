import { CenterRotatable, CenterRotatableView, CenterRotatableData } from "./center_rotatable";
import { PointGeometry, RectGeometry } from "../../core/geometry";
import { Arrayable, FloatArray, ScreenArray } from "../../core/types";
import * as types from "../../core/types";
import * as p from "../../core/properties";
import { Context2d } from "../../core/util/canvas";
import { Selection } from "../selections/selection";
import { Scale } from "../scales/scale";
import { Corners } from "../../core/util/bbox";
import { BorderRadius } from "../common/kinds";
export type RectData = CenterRotatableData & {
    sx0: ScreenArray;
    sy1: ScreenArray;
    ssemi_diag: ScreenArray;
    max_x2_ddist: number;
    max_y2_ddist: number;
    border_radius: Corners<number>;
};
export interface RectView extends RectData {
}
export declare class RectView extends CenterRotatableView {
    model: Rect;
    visuals: Rect.Visuals;
    lazy_initialize(): Promise<void>;
    protected _set_data(indices: number[] | null): void;
    protected _map_data(): void;
    protected _render(ctx: Context2d, indices: number[], data?: RectData): void;
    protected _hit_rect(geometry: RectGeometry): Selection;
    protected _hit_point(geometry: PointGeometry): Selection;
    protected _map_dist_corner_for_data_side_length(coord: Arrayable<number>, side_length: p.Uniform<number>, scale: Scale): [ScreenArray, ScreenArray];
    protected _ddist(dim: 0 | 1, spts: FloatArray, spans: FloatArray): FloatArray;
    draw_legend_for_index(ctx: Context2d, bbox: types.Rect, index: number): void;
}
export declare namespace Rect {
    type Attrs = p.AttrsOf<Props>;
    type Props = CenterRotatable.Props & {
        border_radius: p.Property<BorderRadius>;
        dilate: p.Property<boolean>;
    };
    type Visuals = CenterRotatable.Visuals;
}
export interface Rect extends Rect.Attrs {
}
export declare class Rect extends CenterRotatable {
    properties: Rect.Props;
    __view_type__: RectView;
    constructor(attrs?: Partial<Rect.Attrs>);
}
//# sourceMappingURL=rect.d.ts.map