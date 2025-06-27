# Chrome DevTools MCP Tools

This document provides a comprehensive overview of all 47 available tools organised by module/category.

## Chrome Management Tools (7 tools)

Tools for starting, connecting to, and managing Chrome browser instances.

### `start_chrome`
Start Chrome with remote debugging enabled.
- **Parameters**: `port` (int), `url` (str), `headless` (bool), `chrome_path` (str), `auto_connect` (bool)
- **Returns**: Chrome startup status and connection details
- **Use case**: Launch Chrome for debugging sessions

### `start_chrome_with_debugging`
Start Chrome with debugging and automatically connect.
- **Parameters**: `port` (int), `url` (str), `headless` (bool), `chrome_path` (str)
- **Returns**: Combined startup, connection, and navigation status
- **Use case**: One-step Chrome launch and connection

### `connect_to_browser`
Connect to an existing Chrome instance.
- **Parameters**: `port` (int)
- **Returns**: Connection status and browser information
- **Use case**: Connect to already running Chrome instance

### `disconnect_from_browser`
Disconnect from Chrome instance.
- **Parameters**: None
- **Returns**: Disconnection status
- **Use case**: Clean disconnection from browser

### `get_browser_info`
Get information about connected browser.
- **Parameters**: None
- **Returns**: Browser version, tabs, and capabilities
- **Use case**: Check browser status and available tabs

### `get_chrome_executable_path`
Find Chrome executable on system.
- **Parameters**: `custom_path` (str)
- **Returns**: Path to Chrome executable
- **Use case**: Locate Chrome installation

### `navigate_to_url`
Navigate browser to specified URL.
- **Parameters**: `url` (str)
- **Returns**: Navigation status
- **Use case**: Load web pages for testing

## Network Monitoring Tools (2 tools)

Tools for monitoring and analysing network requests.

### `get_network_requests`
Retrieve captured network requests with filtering.
- **Parameters**: `filter_domain` (str), `filter_status` (int), `limit` (int)
- **Returns**: Filtered list of network requests
- **Use case**: Analyse API calls, resource loading, and network performance

### `get_network_response`
Get detailed response data for specific request.
- **Parameters**: `request_id` (str)
- **Returns**: Complete response including headers and body
- **Use case**: Inspect response content and headers

## Console Tools (6 tools)

Tools for monitoring console output and executing JavaScript.

### `get_console_logs`
Retrieve browser console logs with filtering.
- **Parameters**: `level` (str), `limit` (int)
- **Returns**: Console messages grouped by type
- **Use case**: Debug JavaScript errors and warnings

### `clear_console`
Clear browser console.
- **Parameters**: None
- **Returns**: Clear operation status
- **Use case**: Reset console state for clean debugging

### `evaluate_javascript`
Execute JavaScript code in browser.
- **Parameters**: `code` (str), `return_by_value` (bool)
- **Returns**: Execution result
- **Use case**: Run debugging scripts and inspect variables

### `get_runtime_properties`
Get properties of JavaScript objects.
- **Parameters**: `object_id` (str)
- **Returns**: Object properties and methods
- **Use case**: Inspect complex JavaScript objects

### `enable_console_monitoring`
Start monitoring console events.
- **Parameters**: None
- **Returns**: Monitoring status
- **Use case**: Begin capturing console output

### `disable_console_monitoring`
Stop monitoring console events.
- **Parameters**: None
- **Returns**: Monitoring status
- **Use case**: End console monitoring session

## DOM Tools (10 tools)

Tools for inspecting and manipulating DOM elements.

### `get_document`
Retrieve DOM document structure.
- **Parameters**: `depth` (int), `pierce` (bool)
- **Returns**: DOM tree with specified depth
- **Use case**: Analyse page structure

### `query_selector`
Find single DOM element by CSS selector.
- **Parameters**: `node_id` (int), `selector` (str)
- **Returns**: Matching element node ID
- **Use case**: Locate specific elements for testing

### `query_selector_all`
Find multiple DOM elements by CSS selector.
- **Parameters**: `node_id` (int), `selector` (str)
- **Returns**: Array of matching element node IDs
- **Use case**: Select multiple elements for bulk operations

### `get_element_attributes`
Get all attributes of DOM element.
- **Parameters**: `node_id` (int)
- **Returns**: Element attributes as key-value pairs
- **Use case**: Inspect element properties

### `get_element_outer_html`
Get outer HTML of DOM element.
- **Parameters**: `node_id` (int)
- **Returns**: Complete HTML markup of element
- **Use case**: Extract element markup

### `get_element_box_model`
Get layout information of DOM element.
- **Parameters**: `node_id` (int)
- **Returns**: Content, padding, border, and margin boxes
- **Use case**: Debug layout and positioning

### `describe_element`
Get detailed information about DOM element.
- **Parameters**: `node_id` (int), `depth` (int)
- **Returns**: Element description with children
- **Use case**: Comprehensive element analysis

### `get_element_at_position`
Find DOM element at screen coordinates.
- **Parameters**: `x` (int), `y` (int)
- **Returns**: Element at specified position
- **Use case**: Test click targets and positioning

### `search_elements`
Search DOM for elements matching query.
- **Parameters**: `query` (str)
- **Returns**: Search results with matching elements
- **Use case**: Find elements by text content or attributes

### `focus_element`
Set focus on DOM element.
- **Parameters**: `node_id` (int)
- **Returns**: Focus operation status
- **Use case**: Test focus behaviour and accessibility

## CSS Tools (10 tools)

Tools for analysing CSS styles and layout.

### `get_computed_styles`
Get computed CSS styles for element.
- **Parameters**: `node_id` (int)
- **Returns**: Complete computed styles with inheritance
- **Use case**: Debug CSS cascading and computed values

### `get_inline_styles`
Get inline CSS styles for element.
- **Parameters**: `node_id` (int)
- **Returns**: Inline style properties
- **Use case**: Inspect element-specific styles

### `get_matched_styles`
Get CSS rules matching element.
- **Parameters**: `node_id` (int)
- **Returns**: Matching CSS rules and selectors
- **Use case**: Understand which CSS rules apply

### `set_element_style`
Modify element's inline style.
- **Parameters**: `node_id` (int), `property_name` (str), `value` (str)
- **Returns**: Style modification status
- **Use case**: Test style changes dynamically

### `add_css_rule`
Add new CSS rule to stylesheet.
- **Parameters**: `selector` (str), `properties` (dict)
- **Returns**: Rule creation status
- **Use case**: Inject CSS for testing

### `get_stylesheets`
Get all CSS stylesheets on page.
- **Parameters**: None
- **Returns**: List of stylesheet information
- **Use case**: Analyse CSS architecture

### `get_stylesheet_text`
Get content of specific stylesheet.
- **Parameters**: `stylesheet_id` (str)
- **Returns**: Complete stylesheet text
- **Use case**: Inspect CSS file contents

### `set_stylesheet_text`
Modify stylesheet content.
- **Parameters**: `stylesheet_id` (str), `text` (str)
- **Returns**: Modification status
- **Use case**: Test CSS changes live

### `force_pseudo_state`
Force CSS pseudo-class state on element.
- **Parameters**: `node_id` (int), `forced_pseudo_classes` (list)
- **Returns**: Pseudo-state status
- **Use case**: Test hover, focus, and active states

### `get_platform_fonts`
Get fonts used by element.
- **Parameters**: `node_id` (int)
- **Returns**: Font information and usage
- **Use case**: Debug font rendering issues

## Storage Tools (9 tools)

Tools for managing browser storage (cookies, localStorage, etc.).

### `get_storage_usage_and_quota`
Get storage usage for origin.
- **Parameters**: `origin` (str)
- **Returns**: Storage usage breakdown and quota
- **Use case**: Monitor storage consumption

### `clear_storage_for_origin`
Clear storage data for origin.
- **Parameters**: `origin` (str), `storage_types` (str)
- **Returns**: Clear operation status
- **Use case**: Reset storage for testing

### `get_all_cookies`
Retrieve all browser cookies.
- **Parameters**: None
- **Returns**: Complete cookie list by domain
- **Use case**: Inspect cookie usage

### `clear_all_cookies`
Delete all browser cookies.
- **Parameters**: None
- **Returns**: Clear operation status
- **Use case**: Reset cookie state

### `set_cookie`
Create or modify browser cookie.
- **Parameters**: `name` (str), `value` (str), `domain` (str), `path` (str), `expires` (float), `http_only` (bool), `secure` (bool), `same_site` (str)
- **Returns**: Cookie creation status
- **Use case**: Test cookie functionality

### `get_storage_key_for_frame`
Get storage key for specific frame.
- **Parameters**: `frame_id` (str)
- **Returns**: Frame storage key
- **Use case**: Debug iframe storage isolation

### `track_cache_storage`
Enable/disable cache storage tracking.
- **Parameters**: `origin` (str), `enable` (bool)
- **Returns**: Tracking status
- **Use case**: Monitor cache storage events

### `track_indexeddb`
Enable/disable IndexedDB tracking.
- **Parameters**: `origin` (str), `enable` (bool)
- **Returns**: Tracking status
- **Use case**: Monitor IndexedDB operations

### `override_storage_quota`
Override storage quota for origin.
- **Parameters**: `origin` (str), `quota_size_mb` (float)
- **Returns**: Quota override status
- **Use case**: Test storage limit behaviour

## Performance Tools (4 tools)

Tools for analysing page performance and metrics.

### `get_page_info`
Get comprehensive page information.
- **Parameters**: None
- **Returns**: Page metrics, performance data, and element counts
- **Use case**: Overall page analysis

### `get_performance_metrics`
Get detailed performance metrics.
- **Parameters**: None
- **Returns**: Resource timing, memory usage, and performance analysis
- **Use case**: Performance profiling and optimisation

### `get_cookies`
Get browser cookies with domain filtering.
- **Parameters**: `domain` (str)
- **Returns**: Filtered cookie list
- **Use case**: Domain-specific cookie analysis

### `evaluate_in_all_frames`
Execute JavaScript in all page frames.
- **Parameters**: `code` (str)
- **Returns**: Results from all frames
- **Use case**: Multi-frame testing and debugging

## Tool Usage Examples

### Debug Network Issues
```javascript
// Get all failed requests
get_network_requests(filter_status=404)
get_network_requests(filter_status=500)

// Inspect specific request
get_network_response("request-id-123")
```

### Inspect Page Elements
```javascript
// Get page structure
get_document(depth=2)

// Find elements
query_selector_all(1, "button")
search_elements("Submit")

// Inspect element
get_element_attributes(node_id)
get_computed_styles(node_id)
```

### Monitor Console Output
```javascript
// Start monitoring
enable_console_monitoring()

// Get recent errors
get_console_logs(level="error", limit=10)
```

### Test Storage Functionality
```javascript
// Check storage usage
get_storage_usage_and_quota("https://example.com")

// Manage cookies
get_all_cookies()
set_cookie("test", "value", "example.com")
```

### Performance Analysis
```javascript
// Get comprehensive metrics
get_page_info()
get_performance_metrics()
```

All tools return standardised responses with `success`, `message`, `timestamp`, and `data` fields for consistent error handling and result processing.