import * as p from "../../../core/properties";
import { UIEvent, MoveEvent } from "../../../core/ui_events";
import { Dimensions, SelectionMode } from "../../../core/enums";
import { XYGlyph } from "../../glyphs/xy_glyph";
import { ColumnarDataSource } from "../../sources/columnar_data_source";
import { GlyphRenderer } from "../../renderers/glyph_renderer";
import { GestureTool, GestureToolView } from "../gestures/gesture_tool";
export type HasXYGlyph = {
    glyph: XYGlyph;
};
export declare abstract class EditToolView extends GestureToolView {
    model: EditTool;
    _basepoint: [number, number] | null;
    _mouse_in_frame: boolean;
    protected _select_mode(ev: UIEvent): SelectionMode;
    _move_enter(_e: MoveEvent): void;
    _move_exit(_e: MoveEvent): void;
    _map_drag(sx: number, sy: number, renderer: GlyphRenderer): [number, number] | null;
    _delete_selected(renderer: GlyphRenderer): void;
    _pop_glyphs(cds: ColumnarDataSource, num_objects: number): void;
    _emit_cds_changes(cds: ColumnarDataSource, redraw?: boolean, clear?: boolean, emit?: boolean): void;
    _drag_points(ev: UIEvent, renderers: (GlyphRenderer & HasXYGlyph)[], dim?: Dimensions): void;
    _pad_empty_columns(cds: ColumnarDataSource, coord_columns: string[]): void;
    _select_event(ev: UIEvent, mode: SelectionMode, renderers: GlyphRenderer[]): GlyphRenderer[];
}
export declare namespace EditTool {
    type Attrs = p.AttrsOf<Props>;
    type Props = GestureTool.Props & {
        empty_value: p.Property<unknown>;
        renderers: p.Property<GlyphRenderer[]>;
    };
}
export interface EditTool extends EditTool.Attrs {
}
export declare abstract class EditTool extends GestureTool {
    properties: EditTool.Props;
    __view_type__: EditToolView;
    constructor(attrs?: Partial<EditTool.Attrs>);
}
//# sourceMappingURL=edit_tool.d.ts.map