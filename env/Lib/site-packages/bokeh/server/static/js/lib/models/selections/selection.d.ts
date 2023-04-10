import { Model } from "../../model";
import * as p from "../../core/properties";
import { SelectionMode } from "../../core/enums";
import type { Glyph, GlyphView } from "../glyphs/glyph";
export type OpaqueIndices = typeof OpaqueIndices["__type__"];
export declare const OpaqueIndices: import("../../core/kinds").Kinds.Arrayable<number>;
export type MultiIndices = {
    [key: string]: OpaqueIndices;
};
export type ImageIndex = {
    index: number;
    i: number;
    j: number;
    flat_index: number;
};
export declare namespace Selection {
    type Attrs = p.AttrsOf<Props>;
    type Props = Model.Props & {
        indices: p.Property<OpaqueIndices>;
        line_indices: p.Property<OpaqueIndices>;
        multiline_indices: p.Property<MultiIndices>;
        image_indices: p.Property<ImageIndex[]>;
        view: p.Property<GlyphView | null>;
        selected_glyphs: p.Property<Glyph[]>;
    };
}
export interface Selection extends Selection.Attrs {
}
export declare class Selection extends Model {
    properties: Selection.Props;
    constructor(attrs?: Partial<Selection.Attrs>);
    get_view(): GlyphView | null;
    get selected_glyph(): Glyph | null;
    add_to_selected_glyphs(glyph: Glyph): void;
    update(selection: Selection, _final?: boolean, mode?: SelectionMode): void;
    clear(): void;
    map(mapper: (index: number) => number): Selection;
    is_empty(): boolean;
    update_through_union(other: Selection): void;
    update_through_intersection(other: Selection): void;
    update_through_subtraction(other: Selection): void;
}
//# sourceMappingURL=selection.d.ts.map