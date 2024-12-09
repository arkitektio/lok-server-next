class ValidatorRegistry:

    def __init__(self):
        self.service_validators = {}
        self.service_description = {}

    def register_validator(
        self, service_name, validator, description="This is a service", logo=None
    ):
        assert (
            service_name not in self.service_validators
        ), f"Service {service_name} already registered. Cannot register twice."
        self.service_validators[service_name] = validator
        self.service_description[service_name] = description

    def validate_service(self, service_name, service):
        if service_name not in self.service_validators:
            raise Exception(f"No validator for service {service_name}")

        return self.service_validators[service_name](service)


validator_registry = ValidatorRegistry()


def get_validator_registry():
    return validator_registry
