import { Geometry } from "../../core/geometry";
import * as p from "../../core/properties";
import { SelectionManager } from "../../core/selection_manager";
import { Signal, Signal0 } from "../../core/signaling";
import { Arrayable } from "../../core/types";
import type { GlyphRenderer } from "../renderers/glyph_renderer";
import { SelectionPolicy } from "../selections/interaction_policy";
import { Selection } from "../selections/selection";
import { DataSource } from "./data_source";
export declare namespace ColumnarDataSource {
    type Attrs = p.AttrsOf<Props>;
    type Props = DataSource.Props & {
        data: p.Property<{
            [key: string]: Arrayable;
        }>;
        selection_policy: p.Property<SelectionPolicy>;
        inspected: p.Property<Selection>;
    };
}
export interface ColumnarDataSource extends ColumnarDataSource.Attrs {
}
export declare abstract class ColumnarDataSource extends DataSource {
    properties: ColumnarDataSource.Props;
    data: {
        [key: string]: Arrayable;
    };
    get_array<T>(key: string): T[];
    _select: Signal0<this>;
    inspect: Signal<[GlyphRenderer, {
        geometry: Geometry;
    }], this>;
    readonly selection_manager: SelectionManager;
    constructor(attrs?: Partial<ColumnarDataSource.Attrs>);
    initialize(): void;
    get_column(name: string): Arrayable | null;
    columns(): string[];
    get_length(soft?: boolean): number | null;
    get length(): number;
    clear(): void;
}
//# sourceMappingURL=columnar_data_source.d.ts.map