import { Context2d } from "../../../core/util/canvas";
import { GlyphView } from "../glyph";
import { ReglWrapper } from "./regl_wrap";
export declare abstract class BaseGLGlyph {
    readonly glyph: GlyphView;
    protected regl_wrapper: ReglWrapper;
    protected nvertices: number;
    protected size_changed: boolean;
    protected data_changed: boolean;
    protected visuals_changed: boolean;
    constructor(regl_wrapper: ReglWrapper, glyph: GlyphView);
    set_data_changed(): void;
    set_visuals_changed(): void;
    render(_ctx: Context2d, indices: number[], mainglyph: GlyphView): boolean;
    abstract draw(indices: number[], mainglyph: GlyphView, trans: Transform): void;
}
export type Transform = {
    pixel_ratio: number;
    width: number;
    height: number;
};
//# sourceMappingURL=base.d.ts.map