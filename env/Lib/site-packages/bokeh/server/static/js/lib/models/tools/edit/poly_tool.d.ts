import * as p from "../../../core/properties";
import { UIEvent } from "../../../core/ui_events";
import { MultiLine } from "../../glyphs/multi_line";
import { Patches } from "../../glyphs/patches";
import { GlyphRenderer } from "../../renderers/glyph_renderer";
import { EditTool, EditToolView, HasXYGlyph } from "./edit_tool";
export interface HasPolyGlyph {
    glyph: MultiLine | Patches;
}
export declare abstract class PolyToolView extends EditToolView {
    model: PolyTool;
    _set_vertices(xs: number[] | number, ys: number[] | number): void;
    _hide_vertices(): void;
    _snap_to_vertex(ev: UIEvent, x: number, y: number): [number, number];
}
export declare namespace PolyTool {
    type Attrs = p.AttrsOf<Props>;
    type Props = EditTool.Props & {
        renderers: p.Property<(GlyphRenderer & HasPolyGlyph)[]>;
        vertex_renderer: p.Property<(GlyphRenderer & HasXYGlyph) | null>;
    };
}
export interface PolyTool extends PolyTool.Attrs {
}
export declare abstract class PolyTool extends EditTool {
    properties: PolyTool.Props;
    __view_type__: PolyToolView;
    renderers: (GlyphRenderer & HasPolyGlyph)[];
    constructor(attrs?: Partial<PolyTool.Attrs>);
}
//# sourceMappingURL=poly_tool.d.ts.map