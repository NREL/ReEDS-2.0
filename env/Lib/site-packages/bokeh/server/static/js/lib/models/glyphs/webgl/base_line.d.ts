import { BaseGLGlyph, Transform } from "./base";
import { Float32Buffer, Uint8Buffer } from "./buffer";
import { ReglWrapper } from "./regl_wrap";
import { GlyphView } from "../glyph";
import * as visuals from "../../../core/visuals";
import { Texture2D } from "regl";
export type LineGLVisuals = {
    readonly line: visuals.LineScalar;
};
export declare abstract class BaseLineGL extends BaseGLGlyph {
    readonly glyph: GlyphView;
    protected _points?: Float32Buffer;
    protected _show?: Uint8Buffer;
    private _antialias;
    private _miter_limit;
    protected _color: number[];
    protected _linewidth: number;
    protected _line_dash: number[];
    protected _is_closed: boolean;
    protected _length_so_far?: Float32Buffer;
    protected _dash_tex?: Texture2D;
    protected _dash_tex_info?: number[];
    protected _dash_scale?: number;
    protected _dash_offset?: number;
    constructor(regl_wrapper: ReglWrapper, glyph: GlyphView);
    abstract draw(_indices: number[], main_glyph: GlyphView, transform: Transform): void;
    protected _draw_impl(indices: number[], transform: Transform, main_gl_glyph: BaseLineGL): void;
    protected abstract _get_show_buffer(indices: number[], main_gl_glyph: BaseLineGL): Uint8Buffer;
    protected abstract _get_visuals(): LineGLVisuals;
    protected _is_dashed(): boolean;
    protected _set_data(): void;
    protected abstract _set_data_points(): Float32Array;
    protected _set_visuals(): void;
}
//# sourceMappingURL=base_line.d.ts.map