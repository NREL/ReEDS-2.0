import { ColumnarDataSource } from "./columnar_data_source";
import { Arrayable, Data } from "../../core/types";
import { PatchSet } from "../../core/patching";
import * as p from "../../core/properties";
export declare namespace ColumnDataSource {
    type Attrs = p.AttrsOf<Props>;
    type Props = ColumnarDataSource.Props & {
        data: p.Property<{
            [key: string]: Arrayable;
        }>;
    };
}
export interface ColumnDataSource extends ColumnDataSource.Attrs {
}
export declare class ColumnDataSource extends ColumnarDataSource {
    properties: ColumnDataSource.Props;
    constructor(attrs?: Partial<ColumnDataSource.Attrs>);
    stream(new_data: Data, rollover?: number, { sync }?: {
        sync?: boolean;
    }): void;
    patch(patches: PatchSet<unknown>, { sync }?: {
        sync?: boolean;
    }): void;
}
//# sourceMappingURL=column_data_source.d.ts.map