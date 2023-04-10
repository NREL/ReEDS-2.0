import { LRTB, LRTBView, LRTBData } from "./lrtb";
import { FloatArray, ScreenArray } from "../../core/types";
import * as p from "../../core/properties";
export type BlockData = LRTBData & {
    _x: FloatArray;
    _y: FloatArray;
    readonly width: p.Uniform<number>;
    readonly height: p.Uniform<number>;
    stop: ScreenArray;
    sbottom: ScreenArray;
    sleft: ScreenArray;
    sright: ScreenArray;
    readonly max_width: number;
};
export interface BlockView extends BlockData {
}
export declare class BlockView extends LRTBView {
    model: Block;
    visuals: Block.Visuals;
    lazy_initialize(): Promise<void>;
    scenterxy(i: number): [number, number];
    protected _lrtb(i: number): [number, number, number, number];
    protected _map_data(): void;
}
export declare namespace Block {
    type Attrs = p.AttrsOf<Props>;
    type Props = LRTB.Props & {
        x: p.CoordinateSpec;
        y: p.CoordinateSpec;
        width: p.NumberSpec;
        height: p.NumberSpec;
    };
    type Visuals = LRTB.Visuals;
}
export interface Block extends Block.Attrs {
}
export declare class Block extends LRTB {
    properties: Block.Props;
    __view_type__: BlockView;
    constructor(attrs?: Partial<Block.Attrs>);
}
//# sourceMappingURL=block.d.ts.map