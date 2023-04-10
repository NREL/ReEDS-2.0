import { Filter } from "./filter";
import * as p from "../../core/properties";
import { Indices } from "../../core/types";
import { ColumnarDataSource } from "../sources/columnar_data_source";
export declare namespace IntersectionFilter {
    type Attrs = p.AttrsOf<Props>;
    type Props = Filter.Props & {
        operands: p.Property<Filter[]>;
    };
}
export interface IntersectionFilter extends IntersectionFilter.Attrs {
}
export declare class IntersectionFilter extends Filter {
    properties: IntersectionFilter.Props;
    constructor(attrs?: Partial<IntersectionFilter.Attrs>);
    compute_indices(source: ColumnarDataSource): Indices;
}
//# sourceMappingURL=intersection_filter.d.ts.map