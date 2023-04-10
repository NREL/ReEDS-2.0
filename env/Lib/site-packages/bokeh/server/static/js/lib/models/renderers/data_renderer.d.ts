import { Renderer, RendererView } from "./renderer";
import { GlyphView } from "../glyphs/glyph";
import { Scale } from "../scales/scale";
import { AutoRanged, auto_ranged } from "../ranges/data_range1d";
import { SelectionManager } from "../../core/selection_manager";
import * as p from "../../core/properties";
import { Rect } from "../../core/types";
export declare abstract class DataRendererView extends RendererView implements AutoRanged {
    model: DataRenderer;
    visuals: DataRenderer.Visuals;
    get xscale(): Scale;
    get yscale(): Scale;
    protected abstract get glyph_view(): GlyphView;
    readonly [auto_ranged] = true;
    bounds(): Rect;
    log_bounds(): Rect;
}
export declare namespace DataRenderer {
    type Attrs = p.AttrsOf<Props>;
    type Props = Renderer.Props;
    type Visuals = Renderer.Visuals;
}
export interface DataRenderer extends DataRenderer.Attrs {
}
export declare abstract class DataRenderer extends Renderer {
    properties: DataRenderer.Props;
    __view_type__: DataRendererView;
    constructor(attrs?: Partial<DataRenderer.Attrs>);
    abstract get_selection_manager(): SelectionManager;
    get selection_manager(): SelectionManager;
}
//# sourceMappingURL=data_renderer.d.ts.map