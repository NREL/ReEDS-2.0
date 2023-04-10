import { DataRenderer, DataRendererView } from "./data_renderer";
import { GlyphRenderer, GlyphRendererView } from "./glyph_renderer";
import { Renderer } from "./renderer";
import { GlyphView } from "../glyphs/glyph";
import * as p from "../../core/properties";
import { IterViews } from "../../core/build_views";
import { SelectionManager } from "../../core/selection_manager";
export declare class ContourRendererView extends DataRendererView {
    model: ContourRenderer;
    fill_view: GlyphRendererView;
    line_view: GlyphRendererView;
    children(): IterViews;
    get glyph_view(): GlyphView;
    lazy_initialize(): Promise<void>;
    remove(): void;
    protected _render(): void;
    renderer_view<T extends Renderer>(renderer: T): T["__view_type__"] | undefined;
}
export declare namespace ContourRenderer {
    type Attrs = p.AttrsOf<Props>;
    type Props = DataRenderer.Props & {
        fill_renderer: p.Property<GlyphRenderer>;
        line_renderer: p.Property<GlyphRenderer>;
        levels: p.Property<number[]>;
    };
}
export interface ContourRenderer extends ContourRenderer.Attrs {
}
export declare class ContourRenderer extends DataRenderer {
    properties: ContourRenderer.Props;
    __view_type__: ContourRendererView;
    constructor(attrs?: Partial<ContourRenderer.Attrs>);
    get_selection_manager(): SelectionManager;
}
//# sourceMappingURL=contour_renderer.d.ts.map