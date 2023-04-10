import { MarkerType } from "../../core/enums";
import { LineVector, FillVector, HatchVector } from "../../core/visuals";
import { Context2d } from "../../core/util/canvas";
type VectorVisuals = {
    line: LineVector;
    fill: FillVector;
    hatch: HatchVector;
};
export type RenderOne = (ctx: Context2d, i: number, r: number, visuals: VectorVisuals) => void;
export declare const marker_funcs: {
    [key in MarkerType]: RenderOne;
};
export {};
//# sourceMappingURL=defs.d.ts.map