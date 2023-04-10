import { Filter } from "./filter";
import * as p from "../../core/properties";
import { Indices } from "../../core/types";
import { ColumnarDataSource } from "../sources/columnar_data_source";
export declare namespace AllIndices {
    type Attrs = p.AttrsOf<Props>;
    type Props = Filter.Props & {};
}
export interface AllIndices extends AllIndices.Attrs {
}
export declare class AllIndices extends Filter {
    properties: AllIndices.Props;
    constructor(attrs?: Partial<AllIndices.Attrs>);
    compute_indices(source: ColumnarDataSource): Indices;
}
//# sourceMappingURL=all_indices.d.ts.map