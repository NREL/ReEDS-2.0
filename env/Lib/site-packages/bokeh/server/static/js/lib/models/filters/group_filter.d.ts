import { Filter } from "./filter";
import * as p from "../../core/properties";
import { Indices } from "../../core/types";
import { ColumnarDataSource } from "../sources/columnar_data_source";
export declare namespace GroupFilter {
    type Attrs = p.AttrsOf<Props>;
    type Props = Filter.Props & {
        column_name: p.Property<string>;
        group: p.Property<string>;
    };
}
export interface GroupFilter extends GroupFilter.Attrs {
}
export declare class GroupFilter extends Filter {
    properties: GroupFilter.Props;
    constructor(attrs?: Partial<GroupFilter.Attrs>);
    compute_indices(source: ColumnarDataSource): Indices;
}
//# sourceMappingURL=group_filter.d.ts.map