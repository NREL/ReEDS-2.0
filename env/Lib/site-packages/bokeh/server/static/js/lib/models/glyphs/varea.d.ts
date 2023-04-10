import { PointGeometry } from "../../core/geometry";
import { FloatArray, ScreenArray } from "../../core/types";
import { Area, AreaView, AreaData } from "./area";
import { Context2d } from "../../core/util/canvas";
import { SpatialIndex } from "../../core/util/spatial";
import * as p from "../../core/properties";
import { Selection } from "../selections/selection";
export type VAreaData = AreaData & {
    _x: FloatArray;
    _y1: FloatArray;
    _y2: FloatArray;
    sx: ScreenArray;
    sy1: ScreenArray;
    sy2: ScreenArray;
};
export interface VAreaView extends VAreaData {
}
export declare class VAreaView extends AreaView {
    model: VArea;
    visuals: VArea.Visuals;
    protected _index_data(index: SpatialIndex): void;
    protected _render(ctx: Context2d, _indices: number[], data?: VAreaData): void;
    scenterxy(i: number): [number, number];
    protected _hit_point(geometry: PointGeometry): Selection;
    protected _map_data(): void;
}
export declare namespace VArea {
    type Attrs = p.AttrsOf<Props>;
    type Props = Area.Props & {
        x: p.CoordinateSpec;
        y1: p.CoordinateSpec;
        y2: p.CoordinateSpec;
    };
    type Visuals = Area.Visuals;
}
export interface VArea extends VArea.Attrs {
}
export declare class VArea extends Area {
    properties: VArea.Props;
    __view_type__: VAreaView;
    constructor(attrs?: Partial<VArea.Attrs>);
}
//# sourceMappingURL=varea.d.ts.map