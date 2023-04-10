import { Transform } from "./base";
import { BaseMarkerGL, MarkerVisuals } from "./base_marker";
import { ReglWrapper } from "./regl_wrap";
import { GlyphView } from "../glyph";
import { MarkerType } from "../../../core/enums";
export declare abstract class SingleMarkerGL extends BaseMarkerGL {
    readonly glyph: GlyphView;
    constructor(regl_wrapper: ReglWrapper, glyph: GlyphView);
    abstract draw(indices: number[], mainglyph: GlyphView, trans: Transform): void;
    protected _draw_impl(indices: number[], transform: Transform, main_gl_glyph: SingleMarkerGL, marker_type: MarkerType | "rect"): void;
    protected abstract _get_visuals(): MarkerVisuals;
    protected abstract _set_data(): void;
}
//# sourceMappingURL=single_marker.d.ts.map