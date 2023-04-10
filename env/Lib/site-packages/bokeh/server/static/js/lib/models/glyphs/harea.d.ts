import { PointGeometry } from "../../core/geometry";
import { FloatArray, ScreenArray } from "../../core/types";
import { Area, AreaView, AreaData } from "./area";
import { Context2d } from "../../core/util/canvas";
import { SpatialIndex } from "../../core/util/spatial";
import * as p from "../../core/properties";
import { Selection } from "../selections/selection";
export type HAreaData = AreaData & {
    _x1: FloatArray;
    _x2: FloatArray;
    _y: FloatArray;
    sx1: ScreenArray;
    sx2: ScreenArray;
    sy: ScreenArray;
};
export interface HAreaView extends HAreaData {
}
export declare class HAreaView extends AreaView {
    model: HArea;
    visuals: HArea.Visuals;
    protected _index_data(index: SpatialIndex): void;
    protected _render(ctx: Context2d, _indices: number[], data?: HAreaData): void;
    protected _hit_point(geometry: PointGeometry): Selection;
    scenterxy(i: number): [number, number];
    protected _map_data(): void;
}
export declare namespace HArea {
    type Attrs = p.AttrsOf<Props>;
    type Props = Area.Props & {
        x1: p.CoordinateSpec;
        x2: p.CoordinateSpec;
        y: p.CoordinateSpec;
    };
    type Visuals = Area.Visuals;
}
export interface HArea extends HArea.Attrs {
}
export declare class HArea extends Area {
    properties: HArea.Props;
    __view_type__: HAreaView;
    constructor(attrs?: Partial<HArea.Attrs>);
}
//# sourceMappingURL=harea.d.ts.map