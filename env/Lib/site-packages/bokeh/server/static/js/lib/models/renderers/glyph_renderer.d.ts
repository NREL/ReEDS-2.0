import { DataRenderer, DataRendererView } from "./data_renderer";
import { Glyph, GlyphView } from "../glyphs/glyph";
import { ColumnarDataSource } from "../sources/columnar_data_source";
import { CDSView, CDSViewView } from "../sources/cds_view";
import { Indices } from "../../core/types";
import * as p from "../../core/properties";
import { HitTestResult } from "../../core/hittest";
import { Geometry } from "../../core/geometry";
import { SelectionManager } from "../../core/selection_manager";
import { IterViews } from "../../core/build_views";
import { Context2d } from "../../core/util/canvas";
import { Decoration } from "../graphics/decoration";
import { Marking } from "../graphics/marking";
export declare class GlyphRendererView extends DataRendererView {
    model: GlyphRenderer;
    cds_view: CDSViewView;
    glyph: GlyphView;
    selection_glyph: GlyphView;
    nonselection_glyph: GlyphView;
    hover_glyph?: GlyphView;
    muted_glyph: GlyphView;
    decimated_glyph: GlyphView;
    get glyph_view(): GlyphView;
    children(): IterViews;
    protected all_indices: Indices;
    protected decimated: Indices;
    protected last_dtrender: number;
    get data_source(): p.Property<ColumnarDataSource>;
    lazy_initialize(): Promise<void>;
    build_glyph_view<T extends Glyph>(glyph: T): Promise<GlyphView>;
    remove(): void;
    private _previous_inspected?;
    connect_signals(): void;
    _update_masked_indices(): Indices;
    update_data(indices?: number[]): void;
    set_data(indices?: number[]): void;
    set_visuals(): void;
    get has_webgl(): boolean;
    protected _render(): void;
    get_reference_point(field: string | null, value?: unknown): number;
    draw_legend(ctx: Context2d, x0: number, x1: number, y0: number, y1: number, field: string | null, label: unknown, index: number | null): void;
    hit_test(geometry: Geometry): HitTestResult;
}
export declare namespace GlyphRenderer {
    type Attrs = p.AttrsOf<Props>;
    type Props = DataRenderer.Props & {
        data_source: p.Property<ColumnarDataSource>;
        view: p.Property<CDSView>;
        glyph: p.Property<Glyph>;
        hover_glyph: p.Property<Glyph | null>;
        nonselection_glyph: p.Property<Glyph | "auto" | null>;
        selection_glyph: p.Property<Glyph | "auto" | null>;
        muted_glyph: p.Property<Glyph | "auto" | null>;
        muted: p.Property<boolean>;
    };
}
export interface GlyphRenderer extends GlyphRenderer.Attrs {
}
export declare class GlyphRenderer extends DataRenderer {
    properties: GlyphRenderer.Props;
    __view_type__: GlyphRendererView;
    constructor(attrs?: Partial<GlyphRenderer.Attrs>);
    get_selection_manager(): SelectionManager;
    add_decoration(marking: Marking, node: "start" | "middle" | "end"): Decoration;
}
//# sourceMappingURL=glyph_renderer.d.ts.map