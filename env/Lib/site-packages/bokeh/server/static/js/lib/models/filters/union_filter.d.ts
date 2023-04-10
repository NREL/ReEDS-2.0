import { Filter } from "./filter";
import * as p from "../../core/properties";
import { Indices } from "../../core/types";
import { ColumnarDataSource } from "../sources/columnar_data_source";
export declare namespace UnionFilter {
    type Attrs = p.AttrsOf<Props>;
    type Props = Filter.Props & {
        operands: p.Property<Filter[]>;
    };
}
export interface UnionFilter extends UnionFilter.Attrs {
}
export declare class UnionFilter extends Filter {
    properties: UnionFilter.Props;
    constructor(attrs?: Partial<UnionFilter.Attrs>);
    compute_indices(source: ColumnarDataSource): Indices;
}
//# sourceMappingURL=union_filter.d.ts.map