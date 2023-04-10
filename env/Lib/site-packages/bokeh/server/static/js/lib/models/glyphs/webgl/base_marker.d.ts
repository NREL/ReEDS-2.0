import { Vec4 } from "regl";
import { BaseGLGlyph, Transform } from "./base";
import { Float32Buffer, Uint8Buffer } from "./buffer";
import { ReglWrapper } from "./regl_wrap";
import { GlyphView } from "../glyph";
import { MarkerType } from "../../../core/enums";
import * as visuals from "../../../core/visuals";
export type MarkerVisuals = {
    readonly line: visuals.LineVector;
    readonly fill: visuals.FillVector;
    readonly hatch: visuals.HatchVector;
};
export declare abstract class BaseMarkerGL extends BaseGLGlyph {
    readonly glyph: GlyphView;
    private _antialias;
    protected _centers?: Float32Buffer;
    protected _widths?: Float32Buffer;
    protected _heights?: Float32Buffer;
    protected _angles?: Float32Buffer;
    protected _border_radius: Vec4;
    protected _show?: Uint8Buffer;
    protected _show_all: boolean;
    private _linewidths?;
    private _line_rgba;
    private _fill_rgba;
    private _line_caps;
    private _line_joins;
    private _have_hatch;
    private _hatch_patterns?;
    private _hatch_scales?;
    private _hatch_weights?;
    private _hatch_rgba?;
    protected static readonly missing_point = -10000;
    constructor(regl_wrapper: ReglWrapper, glyph: GlyphView);
    abstract draw(indices: number[], mainglyph: GlyphView, trans: Transform): void;
    protected _draw_one_marker_type(marker_type: MarkerType | "rect", transform: Transform, main_gl_glyph: BaseMarkerGL): void;
    protected abstract _get_visuals(): MarkerVisuals;
    protected abstract _set_data(): void;
    protected _set_visuals(): void;
}
//# sourceMappingURL=base_marker.d.ts.map