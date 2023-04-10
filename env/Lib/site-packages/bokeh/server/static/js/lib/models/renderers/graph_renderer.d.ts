import { DataRenderer, DataRendererView } from "./data_renderer";
import { GlyphRenderer, GlyphRendererView } from "./glyph_renderer";
import { Renderer } from "./renderer";
import { GlyphView } from "../glyphs/glyph";
import { LayoutProvider } from "../graphs/layout_provider";
import { GraphHitTestPolicy } from "../graphs/graph_hit_test_policy";
import * as p from "../../core/properties";
import { IterViews } from "../../core/build_views";
import { SelectionManager } from "../../core/selection_manager";
export declare class GraphRendererView extends DataRendererView {
    model: GraphRenderer;
    edge_view: GlyphRendererView;
    node_view: GlyphRendererView;
    get glyph_view(): GlyphView;
    children(): IterViews;
    lazy_initialize(): Promise<void>;
    connect_signals(): void;
    protected apply_coordinates(): void;
    remove(): void;
    protected _render(): void;
    renderer_view<T extends Renderer>(renderer: T): T["__view_type__"] | undefined;
}
export declare namespace GraphRenderer {
    type Attrs = p.AttrsOf<Props>;
    type Props = DataRenderer.Props & {
        layout_provider: p.Property<LayoutProvider>;
        node_renderer: p.Property<GlyphRenderer>;
        edge_renderer: p.Property<GlyphRenderer>;
        selection_policy: p.Property<GraphHitTestPolicy>;
        inspection_policy: p.Property<GraphHitTestPolicy>;
    };
}
export interface GraphRenderer extends GraphRenderer.Attrs {
}
export declare class GraphRenderer extends DataRenderer {
    properties: GraphRenderer.Props;
    __view_type__: GraphRendererView;
    constructor(attrs?: Partial<GraphRenderer.Attrs>);
    get_selection_manager(): SelectionManager;
}
//# sourceMappingURL=graph_renderer.d.ts.map