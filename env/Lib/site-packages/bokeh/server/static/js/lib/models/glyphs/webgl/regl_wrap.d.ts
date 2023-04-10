import { BoundingBox, Buffer, BufferOptions } from "regl";
import { DashReturn } from "./dash_cache";
import { MarkerType } from "../../../core/enums";
export declare function get_regl(gl: WebGLRenderingContext): ReglWrapper;
type ReglRenderFunction = ({}: {}) => void;
export declare class ReglWrapper {
    private _regl;
    private _regl_available;
    private _dash_cache?;
    private _solid_line?;
    private _dashed_line?;
    private _marker_no_hatch_map?;
    private _marker_hatch_map?;
    private _line_geometry;
    private _line_triangles;
    private _scissor;
    private _viewport;
    constructor(gl: WebGLRenderingContext);
    buffer(options: BufferOptions): Buffer;
    clear(width: number, height: number): void;
    get has_webgl(): boolean;
    get scissor(): BoundingBox;
    set_scissor(x: number, y: number, width: number, height: number): void;
    get viewport(): BoundingBox;
    dashed_line(): ReglRenderFunction;
    get_dash(line_dash: number[]): DashReturn;
    marker_no_hatch(marker_type: MarkerType | "rect"): ReglRenderFunction;
    marker_hatch(marker_type: MarkerType | "rect"): ReglRenderFunction;
    solid_line(): ReglRenderFunction;
}
export {};
//# sourceMappingURL=regl_wrap.d.ts.map