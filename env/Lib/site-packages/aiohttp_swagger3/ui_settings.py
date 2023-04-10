import re
from typing import Dict, List, Optional, Union

import attr

HEX_COLOR_REGEX = re.compile(r"^#([a-f0-9]{3,4}|[a-f0-9]{4}(?:[a-f0-9]{2}){1,2})$", re.IGNORECASE)


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True, kw_only=True)
class _UiSettings:
    path: str

    def to_settings(self) -> Dict:
        return attr.asdict(self, filter=attr.filters.exclude(attr.fields(_UiSettings).path))


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True, kw_only=True)
class SwaggerUiSettings(_UiSettings):
    """Settings for `Swagger UI <https://swagger.io/tools/swagger-ui/>`_, see: `configuration <https://github.com/swagger-api/swagger-ui/blob/master/docs/usage/configuration.md>`__

    :param str layout: The name of a component available via the plugin system to use as the top-level
        layout for Swagger UI. It must be either ``BaseLayout`` or ``StandaloneLayout``. Default ``StandaloneLayout``.
    :param bool deepLinking: If set to ``True``, enables deep linking for tags and operations. See the
        `Deep Linking documentation <https://github.com/swagger-api/swagger-ui/blob/master/docs/usage/deep-linking.md>`_
        for more information. Default ``True``.
    :param bool displayOperationId: Controls the display of operationId in operations list. Default ``False``.
    :param int defaultModelsExpandDepth: The default expansion depth for models
        (set to ``-1`` completely hide the models). Default ``1``.
    :param int defaultModelExpandDepth: The default expansion depth for the model on the
        model-example section. Default ``1``.
    :param int defaultModelRendering: Controls how the model is shown when the API is first rendered.
        It must be either ``example`` or ``model``. Default ``example``.
    :param bool displayRequestDuration: Controls the display of the request duration (in milliseconds) for
        "Try it out" requests. Default ``False``.
    :param str docExpansion: Controls the default expansion setting for the operations and tags.
        It can be ``list`` (expands only the tags), ``full`` (expands the tags and operations) or
        ``none`` (expands nothing). Default ``list``.
    :param bool filter: If set, enables filtering. The top bar will show an edit box that you can use to filter
        the tagged operations that are shown. Default ``False``.
    :param bool showExtensions: Controls the display of vendor extension (x-) fields and values for
        Operations, Parameters, and Schema. Default ``False``.
    :param bool showCommonExtensions:  Controls the display of extensions (pattern, maxLength,
        minLength, maximum, minimum) fields and values for Parameters. Default ``False``.
    :param list supportedSubmitMethods: List of HTTP methods that have the "Try it out" feature enabled.
        An empty array disables "Try it out" for all operations. This does not filter the operations from the display.
        Available methods: ``get``, ``put``, ``post``, ``delete``, ``options``, ``head``, ``patch``, ``trace``.
        By default all methods are enabled.
    :param str validatorUrl: By default, Swagger UI attempts to validate specs against swagger.io's online validator.
        You can use this parameter to set a different validator URL, for example for locally deployed
        validators (Validator Badge). Setting it to ``None`` will disable validation.
        Default ``https://validator.swagger.io/validator``.
    :param bool withCredentials: If set to ``True``, enables passing credentials,
        `as defined in the Fetch standard <https://fetch.spec.whatwg.org/#credentials>`_,
        in CORS requests that are sent by the browser. Note that Swagger UI cannot currently set cookies cross-domain
        (see `swagger-js#1163 <https://github.com/swagger-api/swagger-js/issues/1163>`_) - as a result,
        you will have to rely on browser-supplied cookies (which this setting enables sending) that
        Swagger UI cannot control. Default ``False``.
    """

    # plugin
    layout: str = attr.attrib(
        default="StandaloneLayout",
        validator=attr.validators.in_(("BaseLayout", "StandaloneLayout")),
    )
    # display
    deepLinking: bool = attr.attrib(default=True, validator=attr.validators.instance_of(bool))
    displayOperationId: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    defaultModelsExpandDepth: int = attr.attrib(default=1, validator=attr.validators.instance_of(int))
    defaultModelExpandDepth: int = attr.attrib(default=1, validator=attr.validators.instance_of(int))
    defaultModelRendering: str = attr.attrib(
        default="example",
        validator=attr.validators.in_(("example", "model")),
    )
    displayRequestDuration: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    docExpansion: str = attr.attrib(
        default="list",
        validator=attr.validators.in_(("list", "full", "none")),
    )
    filter: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    showExtensions: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    showCommonExtensions: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    # network
    supportedSubmitMethods: List[str] = attr.attrib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.in_(("get", "put", "post", "delete", "options", "head", "patch", "trace")),
            iterable_validator=attr.validators.instance_of(list),
        )
    )
    validatorUrl: Optional[str] = attr.attrib(
        default="https://validator.swagger.io/validator",
        validator=attr.validators.optional(attr.validators.instance_of(str)),  # type: ignore
    )

    withCredentials: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))

    # noinspection PyUnresolvedReferences
    @supportedSubmitMethods.default
    def _supported_submit_methods_default(self) -> List[str]:
        return ["get", "put", "post", "delete", "options", "head", "patch", "trace"]


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True, kw_only=True)
class ReDocUiSettings(_UiSettings):
    """Settings for `ReDoc UI <https://redocly.github.io/redoc/>`_, see: `ReDoc options <https://github.com/Redocly/redoc#redoc-options-object>`__

    :param bool disableSearch: Disable search indexing and search box. Default ``False``.
    :param bool expandDefaultServerVariables: Enable expanding default server variables. Default ``False``.
    :param str expandResponses: Specify which responses to expand by default by response codes. Values should be passed
        as comma-separated list without spaces e.g. ``200,201``. Special value ``all`` expands all responses by default.
        Be careful: this option can slow-down documentation rendering time. Default is empty string.
    :param int maxDisplayedEnumValues: Display only specified number of enum values. Hide rest values under spoiler.
        Default ``2``.
    :param bool hideDownloadButton: Do not show "Download" spec button. **THIS DOESN'T MAKE YOUR SPEC PRIVATE**,
        it just hides the button. Default ``False``.
    :param bool hideHostname: If set, the protocol and hostname is not shown in the operation
        definition. Default ``False``.
    :param bool hideLoading: Do not show loading animation. Useful for small docs. Default ``False``.
    :param bool hideSingleRequestSampleTab: Do not show the request sample tab for requests with only one sample.
        Default ``False``.
    :param bool expandSingleSchemaField: Automatically expand single field in a schema. Default ``False``.
    :param int,str jsonSampleExpandLevel: Set the default expand level for JSON payload samples (responses and
        request body). Special value ``all`` expands all levels. Default ``2``.
    :param bool hideSchemaTitles: Do not display schema ``title`` next to to the type. Default ``False``.
    :param bool simpleOneOfTypeLabel: Show only unique oneOf types in the label without titles. Default ``False``.
    :param bool menuToggle: If ``True`` clicking second time on expanded menu item will collapse it. Default ``True``.
    :param bool nativeScrollbars: Use native scrollbar for sidemenu instead of perfect-scroll (scrolling performance
        optimization for big specs). Default ``False``.
    :param bool noAutoAuth: Do not inject Authentication section automatically. Default ``False``.
    :param bool onlyRequiredInSamples: Shows only required fields in request samples. Default ``False``.
    :param bool pathInMiddlePanel: Show path link and HTTP verb in the middle panel instead of the right one.
        Default ``False``.
    :param bool requiredPropsFirst: Show required properties first ordered in the same order as in ``required`` array.
        Default ``False``.
    :param int scrollYOffset: If set, specifies a vertical scroll-offset. This is often useful when there are fixed
        positioned elements at the top of the page, such as navbars, headers, etc. Default ``0``.
    :param bool showExtensions: Show vendor extensions ("x-" fields). Extensions used by ReDoc are ignored.
        Default ``False``.
    :param bool sortPropsAlphabetically: Sort properties alphabetically. Default ``False``.
    :param bool sortEnumValuesAlphabetically: Sort enum values alphabetically. Default ``False``.
    :param bool suppressWarnings: If set, warnings are not rendered at the top of documentation
        (they still are logged to the console). Default ``False``.
    :param int payloadSampleIdx: If set, payload sample will be inserted at this index or last. Indexes start from 0.
        Default ``0``.
    :param bool untrustedSpec: If set, the spec is considered untrusted and all HTML/markdown is sanitized to prevent
        XSS. Disabled by default for performance reasons. **Enable this option if you work with untrusted user data!**
        Default ``False``.
    """

    disableSearch: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    expandDefaultServerVariables: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    expandResponses: str = attr.attrib(default="", validator=attr.validators.instance_of(str))
    maxDisplayedEnumValues: int = attr.attrib(default=2, validator=attr.validators.instance_of(int))
    hideDownloadButton: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    hideHostname: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    hideLoading: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    hideSingleRequestSampleTab: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    expandSingleSchemaField: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    jsonSampleExpandLevel: Union[int, str] = attr.attrib(default=2, validator=attr.validators.instance_of((int, str)))
    hideSchemaTitles: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    simpleOneOfTypeLabel: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    menuToggle: bool = attr.attrib(default=True, validator=attr.validators.instance_of(bool))
    nativeScrollbars: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    noAutoAuth: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    onlyRequiredInSamples: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    pathInMiddlePanel: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    requiredPropsFirst: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    scrollYOffset: int = attr.attrib(default=0, validator=attr.validators.instance_of(int))
    showExtensions: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    sortPropsAlphabetically: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    sortEnumValuesAlphabetically: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    suppressWarnings: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    payloadSampleIdx: int = attr.attrib(default=0, validator=attr.validators.instance_of(int))
    untrustedSpec: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))

    # noinspection PyUnresolvedReferences
    @expandResponses.validator
    def _expand_responses_validator(self, _: "attr.Attribute[str]", value: str) -> None:
        if value in ("all", ""):
            return
        raw_codes = value.split(",")
        for raw_code in raw_codes:
            try:
                int(raw_code)
            except ValueError:
                raise ValueError(
                    "expandResponses must be either 'all' or " f"comma-separated list of http codes, got '{raw_code}'"
                )

    # noinspection PyUnresolvedReferences
    @jsonSampleExpandLevel.validator
    def _json_sample_expand_level_validator(self, _: "attr.Attribute[Union[int, str]]", value: Union[int, str]) -> None:
        if isinstance(value, str) and value != "all":
            raise ValueError(f"jsonSampleExpandLevel must be either 'all' or integer, got '{value}'")


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True, kw_only=True)
class RapiDocUiSettings(_UiSettings):
    """Settings for `RapiDoc UI <https://mrin9.github.io/RapiDoc/index.html>`_, see: `RapiDoc API <https://mrin9.github.io/RapiDoc/api.html>`__

    :param bool sort_tags: List APIs sorted by tags. Default ``False``.
    :param str sort_endpoints_by: Sort endpoints within each tags by ``path`` or ``method``. Default ``path``.
    :param str heading_text: Heading Text on top-left corner. (Optional)
    :param str theme: Is the base theme, which is used for calculating colors for various UI components.
        ``theme``, ``bg-color`` and ``text-color`` are the base attributes for generating a custom theme.
        It can be either ``light`` or ``dark``. Default ``light``.
    :param str bg_color: Hex color code for main background. Default ``#fff`` if ``theme`` is ``light``,
        ``#333`` otherwise.
    :param str text_color: Hex color code for text. Default ``#444`` if ``theme`` is ``light``, ``#bbb`` otherwise.
    :param str header_color: Hex color code for the header's background. Default ``#444444``.
    :param str primary_color: Hex color code on various controls such as buttons, tabs. Default ``#FF791A``.
    :param str font_size: Controls the relative font-sizing for the entire document.
        Values are ``default``, ``large`` and ``largest``.
    :param bool use_path_in_nav_bar: Show API paths in the navigation bar instead of summary/description. Default ``False``.
    :param str nav_bg_color: Navigation bar's background color. (optional)
    :param str nav_text_color: Navigation bar's Text color. (optional)
    :param str nav_hover_bg_color: Background color of the navigation item on mouse-over. (optional)
    :param str nav_hover_text_color: Text color of the navigation item on mouse-over. (optional)
    :param str nav_accent_color: Current selected item indicator. (optional)
    :param str layout: Layout helps in placement of request/response sections. In ``column`` layout, request & response
        sections are placed one below the other, In ``row`` layout they are placed side by side. This attribute is
        applicable only when the device width is more than 768px and the render-style is ``view``. Default ``row``.
    :param str render_style: Determines display of api-docs. Currently there are three modes supported. ``read`` - more
        suitable for reading, ``view`` more friendly for quick exploring and ``focused`` show one operation at a time.
        Default ``view``.
    :param str schema_style: Two different ways to display object-schemas in the responses and request bodies.
        It must be either ``tree`` or ``table``. Default ``tree``.
    :param int schema_expand_level: Schema's are expanded by default, use this attribute to control how many levels
        in the schema should be expanded. Default ``999``.
    :param bool schema_description_expanded: Constraint and descriptions information of fields in the schema are
        collapsed to show only the first line. Set it to ``True`` if you want them to fully expanded. Default ``False``.
    :param str default_schema_tab: The schemas are displayed in two tabs - ``model`` and ``example``. This option
        allows you to pick the default tab that you would like to be active. Default ``model``.
    :param bool show_info: Show/hide the documents info section. Default ``True``.
    :param bool show_components: Show/hide the components section both in document and menu. Default ``False``.
    :param bool show_header: Show/hide the header. If you dont want your user to open any other api spec,
        other than the current one, then set this attribute to ``False``. Default ``True``.
    :param bool allow_authentication: Authentication feature, allows the user to select one of the authentication
        mechanism that's available in the spec. Default ``True``.
    :param bool allow_spec_url_load: If set to ``False``, user will not be able to load any spec url from the UI.
        Default ``True``.
    :param bool allow_spec_file_load: If set to ``False``, user will not be able to load any spec file from the local
        drive. This attribute is applicable only when the device width is more than 768px, else this feature is not
        available. Default ``True``.
    :param bool allow_search: If set to ``False``, user will not be able to search APIs. Default ``True``.
    :param bool allow_try: 'TRY' feature allows you to make REST calls to the API server. To disable this feature set
        it to ``False``. Default ``True``.
    :param bool allow_server_selection: If set to ``False``, user will not be able to select API server. The URL
        specified in the server-url attribute will be used if set, else the first server in the API specification file
        will be used. Default ``True``.
    :param str api_key_name: Name of the API key that will be send while trying out the APIs. Default ``Authorization``.
    :param str api_key_value: Value of the API key that will be send while trying out the APIs. This can also be
        provided/overwritten from UI. (optional)
    :param str api_key_location: Determines how you want to send the api-key. It must be either ``header`` or ``query``.
        Default ``header``.
    :param str server_url: OpenAPI spec has a provision for providing the server url. (optional)
    :param str default_api_server: If you have multiple api-server listed in the spec, use this attribute to select the
        default API server, where all the API calls will goto. This can be changed later from the UI. (optional)
    """

    # General
    sort_tags: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    sort_endpoints_by: str = attr.attrib(
        default="path",
        validator=attr.validators.in_(("path", "method")),
    )
    heading_text: Optional[str] = attr.attrib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )
    # UI Colors and Fonts
    theme: str = attr.attrib(
        default="light",
        validator=attr.validators.in_(("light", "dark")),
    )
    bg_color: str = attr.attrib(validator=attr.validators.instance_of(str))
    text_color: str = attr.attrib(validator=attr.validators.instance_of(str))
    header_color: str = attr.attrib(
        default="#444444",
        validator=attr.validators.instance_of(str),
    )
    primary_color: str = attr.attrib(
        default="#FF791A",
        validator=attr.validators.instance_of(str),
    )
    font_size: str = attr.attrib(
        default="default",
        validator=attr.validators.in_(("default", "large", "largest")),
    )
    # Navigation bar colors
    use_path_in_nav_bar: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    nav_bg_color: Optional[str] = attr.attrib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )
    nav_text_color: Optional[str] = attr.attrib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )
    nav_hover_bg_color: Optional[str] = attr.attrib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )
    nav_hover_text_color: Optional[str] = attr.attrib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )
    nav_accent_color: Optional[str] = attr.attrib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )
    # UI Layout & Placement
    layout: str = attr.attrib(
        default="row",
        validator=attr.validators.in_(("row", "column")),
    )
    render_style: str = attr.attrib(
        default="view",
        validator=attr.validators.in_(("read", "view", "focused")),
    )
    schema_style: str = attr.attrib(
        default="tree",
        validator=attr.validators.in_(("tree", "table")),
    )
    schema_expand_level: int = attr.attrib(default=999, validator=attr.validators.instance_of(int))
    schema_description_expanded: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    default_schema_tab: str = attr.attrib(
        default="model",
        validator=attr.validators.in_(("model", "example")),
    )
    # Hide/Show Sections
    show_info: bool = attr.attrib(default=True, validator=attr.validators.instance_of(bool))
    show_components: bool = attr.attrib(default=False, validator=attr.validators.instance_of(bool))
    show_header: bool = attr.attrib(default=True, validator=attr.validators.instance_of(bool))
    allow_authentication: bool = attr.attrib(default=True, validator=attr.validators.instance_of(bool))
    allow_spec_url_load: bool = attr.attrib(default=True, validator=attr.validators.instance_of(bool))
    allow_spec_file_load: bool = attr.attrib(default=True, validator=attr.validators.instance_of(bool))
    allow_search: bool = attr.attrib(default=True, validator=attr.validators.instance_of(bool))
    allow_try: bool = attr.attrib(default=True, validator=attr.validators.instance_of(bool))
    allow_server_selection: bool = attr.attrib(default=True, validator=attr.validators.instance_of(bool))
    # API Server
    api_key_name: str = attr.attrib(
        default="Authorization",
        validator=attr.validators.instance_of(str),
    )
    api_key_value: Optional[str] = attr.attrib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )
    api_key_location: str = attr.attrib(
        default="header",
        validator=attr.validators.in_(("header", "query")),
    )
    server_url: Optional[str] = attr.attrib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )
    default_api_server: Optional[str] = attr.attrib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )

    # noinspection PyUnresolvedReferences
    @bg_color.validator
    def _bg_color_validator(self, _: "attr.Attribute[str]", value: str) -> None:
        if not HEX_COLOR_REGEX.match(value):
            raise ValueError("bg_color must be valid HEX color")

    # noinspection PyUnresolvedReferences
    @bg_color.default
    def _bg_color_default(self) -> str:
        if self.theme == "light":
            return "#fff"
        return "#333"

    # noinspection PyUnresolvedReferences
    @text_color.validator
    def _text_color_validator(self, _: "attr.Attribute[str]", value: str) -> None:
        if not HEX_COLOR_REGEX.match(value):
            raise ValueError("text_color must be valid HEX color")

    # noinspection PyUnresolvedReferences
    @text_color.default
    def _text_color_default(self) -> str:
        if self.theme == "light":
            return "#444"
        return "#bbb"

    @nav_bg_color.validator
    def _nav_bg_color_validator(self, _: "attr.Attribute[Optional[str]]", value: Optional[str]) -> None:
        if value is not None and not HEX_COLOR_REGEX.match(value):
            raise ValueError("nav_bg_color must be valid HEX color")

    @nav_text_color.validator
    def _nav_text_color_validator(self, _: "attr.Attribute[Optional[str]]", value: Optional[str]) -> None:
        if value is not None and not HEX_COLOR_REGEX.match(value):
            raise ValueError("nav_text_color must be valid HEX color")

    @nav_hover_bg_color.validator
    def _nav_hover_bg_color_validator(self, _: "attr.Attribute[Optional[str]]", value: Optional[str]) -> None:
        if value is not None and not HEX_COLOR_REGEX.match(value):
            raise ValueError("nav_hover_bg_color must be valid HEX color")

    @nav_hover_text_color.validator
    def _nav_hover_text_color_validator(self, _: "attr.Attribute[Optional[str]]", value: Optional[str]) -> None:
        if value is not None and not HEX_COLOR_REGEX.match(value):
            raise ValueError("nav_hover_text_color must be valid HEX color")

    @nav_accent_color.validator
    def _nav_accent_color_validator(self, _: "attr.Attribute[Optional[str]]", value: Optional[str]) -> None:
        if value is not None and not HEX_COLOR_REGEX.match(value):
            raise ValueError("nav_accent_color must be valid HEX color")

    def to_settings(self) -> Dict:
        settings = {}
        attrs = attr.fields(self.__class__)
        for attribute in attrs:
            if attribute.name == "path":
                continue
            value = getattr(self, attribute.name)
            if value is None:
                continue
            settings[attribute.name.replace("_", "-")] = value
        return settings
