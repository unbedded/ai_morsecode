# Universal Validation Framework - Design Plan

## 🎯 **Vision Statement**
**Extract validation logic from configuration system into standalone validation framework that works identically in Python and C++, enabling bulletproof interface validation for ANY API or system boundary.**

---

## 🏗️ **Architecture Overview**

### **Core Concept**
Move from configuration-specific `CfgField` to universal `Field` that validates any data at any interface:
- API request/response validation
- Database input validation
- File format parsing validation
- Inter-service communication validation
- User input validation (CLI, forms, etc.)

### **C++ Compatibility Priority**
All design decisions prioritize seamless C++ translation with identical patterns and capabilities.

---

## 📋 **Key Design Decisions**

### **1. Field Definition Structure**

**Python Version:**
```python
@dataclass
class Field:
    type: FieldType                    # Core type (INT, DOUBLE, STRING, BOOL, ENUM)
    default: Any                       # Default value
    min: Optional[Any] = None          # Range validation (numeric types)
    max: Optional[Any] = None          # Range validation (numeric types)
    choices: Optional[List] = None     # Enum/choice validation
    regex: Optional[str] = None        # String pattern validation
    unit: Optional[str] = None         # Physical unit metadata
    description: str = ""              # Human-readable description
    required: bool = True              # Whether field is mandatory
```

**C++ Translation:**
```cpp
struct Field {
    FieldType type;
    std::any default_value;
    std::optional<std::any> min;
    std::optional<std::any> max;
    std::optional<std::vector<std::any>> choices;
    std::optional<std::string> regex;
    std::optional<std::string> unit;
    std::string description;
    bool required = true;
};
```

**Decision Points:**
- **std::any vs templates**: std::any for runtime flexibility vs template<T> for compile-time safety
- **Validation strategy**: Runtime validation vs compile-time validation
- **Error handling**: Exceptions vs error codes vs std::expected

### **2. Type System Design**

**Python Enum:**
```python
class FieldType(Enum):
    INT = "int"
    DOUBLE = "double"
    STRING = "string"
    BOOL = "bool"
    ENUM = "enum"
    ARRAY = "array"           # New: List/vector support
    OBJECT = "object"         # New: Nested object support
```

**C++ Translation:**
```cpp
enum class FieldType {
    INT,
    DOUBLE,
    STRING,
    BOOL,
    ENUM,
    ARRAY,
    OBJECT
};
```

**Decision Points:**
- **Numeric precision**: int32 vs int64, float vs double defaults
- **String encoding**: UTF-8 handling in C++
- **Array validation**: Homogeneous vs heterogeneous arrays
- **Object nesting**: Depth limits, circular reference prevention

### **3. Validation Engine Architecture**

**Interface Design:**
```python
class Validator:
    def validate(self, data: Any, field: Field) -> ValidationResult:
        """Validate single field against data"""

    def validate_object(self, data: dict, schema: dict[str, Field]) -> ValidationResult:
        """Validate entire object against schema"""

class ValidationResult:
    success: bool
    value: Any                    # Converted/coerced value
    errors: List[ValidationError] # Detailed error information
```

**C++ Translation:**
```cpp
class Validator {
public:
    ValidationResult validate(const std::any& data, const Field& field);
    ValidationResult validate_object(const std::map<std::string, std::any>& data,
                                   const std::map<std::string, Field>& schema);
};

struct ValidationResult {
    bool success;
    std::any value;
    std::vector<ValidationError> errors;
};
```

### **4. Error Handling Strategy**

**Python Approach:**
```python
class ValidationError:
    field_name: str
    error_type: ErrorType        # TYPE_MISMATCH, RANGE_ERROR, PATTERN_ERROR, etc.
    message: str                 # Human-readable error
    expected: str                # What was expected
    actual: str                  # What was received
    path: List[str]              # Field path for nested objects
```

**C++ Translation Options:**

**Option A: Exception-based (Traditional C++)**
```cpp
class ValidationException : public std::exception {
    std::vector<ValidationError> errors;
    // Throw on validation failure
};
```

**Option B: Result-based (Modern C++)**
```cpp
using ValidationResult = std::expected<std::any, std::vector<ValidationError>>;
// Return success/error without exceptions
```

**Decision Points:**
- **Exception vs result types**: Performance vs convenience trade-offs
- **Error aggregation**: Fail-fast vs collect-all-errors strategies
- **Internationalization**: Multi-language error messages

### **5. Cross-Language Serialization**

**Shared Schema Format (JSON Schema compatible):**
```json
{
  "frequency_hz": {
    "type": "int",
    "default": 600,
    "min": 200,
    "max": 2000,
    "unit": "Hz",
    "description": "Target frequency for detection"
  },
  "mode": {
    "type": "enum",
    "choices": ["AUTO", "MANUAL", "ADAPTIVE"],
    "default": "AUTO",
    "description": "Processing mode"
  }
}
```

**Benefits:**
- Language-agnostic schema definitions
- Tooling compatibility (JSON Schema validators)
- Runtime schema loading from files
- API documentation generation

---

## 🚀 **Implementation Phases**

### **Phase 1: Core Validation Engine**
- [ ] Define Field structure with C++ compatibility
- [ ] Implement basic type validation (INT, DOUBLE, STRING, BOOL)
- [ ] Add range validation for numeric types
- [ ] Create ValidationResult and ValidationError types
- [ ] Design error handling strategy (exceptions vs results)

### **Phase 2: Advanced Validation**
- [ ] Implement regex pattern validation for strings
- [ ] Add enum/choice validation
- [ ] Create unit metadata support
- [ ] Implement array validation with type constraints
- [ ] Add nested object validation support

### **Phase 3: C++ Implementation**
- [ ] Translate core Field structures to C++
- [ ] Implement validation engine in C++
- [ ] Create JSON schema serialization/deserialization
- [ ] Ensure API parity between Python and C++ versions
- [ ] Performance optimization for C++ implementation

### **Phase 4: Integration and Testing**
- [ ] Extract validation from config system
- [ ] Create config-system wrapper using validation framework
- [ ] Implement API request validation example
- [ ] Create comprehensive test suites for both languages
- [ ] Performance benchmarking and optimization

---

## 🔍 **Research Requirements**

### **Existing Framework Analysis**
- **Pydantic**: FastAPI integration, performance characteristics, C++ portability
- **Cerberus**: Lightweight design, validation rule flexibility
- **JSON Schema**: Standard compliance, tooling ecosystem
- **OpenAPI**: API validation patterns, code generation capabilities

### **C++ Validation Libraries**
- **nlohmann/json**: JSON parsing and validation capabilities
- **jsoncons**: JSON Schema validation support
- **Boost.PropertyTree**: Configuration-style validation
- **Custom implementations**: Performance and simplicity trade-offs

### **Performance Considerations**
- **Validation overhead**: Acceptable performance cost for validation
- **Memory usage**: Field definition storage efficiency
- **Compilation time**: Template vs runtime trade-offs in C++

---

## 🎯 **Success Criteria**

### **Functional Requirements**
- [ ] Identical validation behavior in Python and C++
- [ ] Support for all common data types and validation rules
- [ ] Clear, actionable error messages with field paths
- [ ] JSON Schema compatibility for interoperability

### **Performance Requirements**
- [ ] Validation overhead < 10% of application processing time
- [ ] Memory usage < 1MB for typical schema definitions
- [ ] C++ compilation time impact < 5% increase

### **Usability Requirements**
- [ ] Intuitive API that feels natural in both languages
- [ ] Comprehensive documentation with examples
- [ ] Easy migration path from existing validation solutions
- [ ] Clear separation between validation framework and config system

---

## 💡 **Open Questions**

### **Design Trade-offs**
1. **Runtime flexibility vs compile-time safety**: How much type safety to sacrifice for flexibility?
2. **Performance vs features**: Which validation features are worth the performance cost?
3. **API surface**: How much functionality to include in core vs extensions?

### **C++ Specific Challenges**
1. **std::any performance**: Is runtime type erasure acceptable for validation use cases?
2. **Error handling philosophy**: Exceptions vs error codes in different domains?
3. **Template complexity**: How to balance compile-time optimization with code simplicity?

### **Ecosystem Integration**
1. **JSON Schema compatibility**: Full compatibility vs subset implementation?
2. **Existing tool integration**: How to work with existing validation ecosystems?
3. **Code generation**: Should schemas generate validation code or use runtime validation?

---

## 📚 **References and Research**

### **Academic Papers**
- Interface validation patterns in distributed systems
- Type system design for cross-language compatibility
- Performance analysis of runtime vs compile-time validation

### **Industry Standards**
- JSON Schema specification and validation patterns
- OpenAPI validation rule implementations
- Protocol buffer validation approaches

### **Open Source Analysis**
- Pydantic internals and performance characteristics
- C++ JSON validation library comparisons
- Cross-language validation framework case studies

---

*This validation framework represents a significant architectural opportunity to create reusable, high-performance validation infrastructure that works identically across Python and C++ ecosystems.*