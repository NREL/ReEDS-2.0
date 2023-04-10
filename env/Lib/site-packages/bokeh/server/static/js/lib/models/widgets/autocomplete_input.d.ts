import { TextInput, TextInputView } from "./text_input";
import { StyleSheetLike } from "../../core/dom";
import * as p from "../../core/properties";
export declare class AutocompleteInputView extends TextInputView {
    model: AutocompleteInput;
    protected _open: boolean;
    protected _last_value: string;
    protected _hover_index: number;
    protected menu: HTMLElement;
    stylesheets(): StyleSheetLike[];
    render(): void;
    change_input(): void;
    protected _update_completions(completions: string[]): void;
    protected _toggle_menu(): void;
    protected _show_menu(): void;
    protected _hide_menu(): void;
    protected _menu_click(event: MouseEvent): void;
    protected _menu_hover(event: MouseEvent): void;
    protected _bump_hover(new_index: number): void;
    _keydown(_event: KeyboardEvent): void;
    protected _keyup(event: KeyboardEvent): void;
}
export declare namespace AutocompleteInput {
    type Attrs = p.AttrsOf<Props>;
    type Props = TextInput.Props & {
        completions: p.Property<string[]>;
        min_characters: p.Property<number>;
        max_completions: p.Property<number | null>;
        case_sensitive: p.Property<boolean>;
        restrict: p.Property<boolean>;
    };
}
export interface AutocompleteInput extends AutocompleteInput.Attrs {
}
export declare class AutocompleteInput extends TextInput {
    properties: AutocompleteInput.Props;
    __view_type__: AutocompleteInputView;
    constructor(attrs?: Partial<AutocompleteInput.Attrs>);
}
//# sourceMappingURL=autocomplete_input.d.ts.map