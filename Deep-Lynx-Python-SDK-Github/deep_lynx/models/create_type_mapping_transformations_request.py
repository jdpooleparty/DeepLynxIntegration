# coding: utf-8

"""
    DeepLynx

    The construction of megaprojects has consistently demonstrated challenges for project managers in regard to meeting cost, schedule, and performance requirements. Megaproject construction challenges are common place within megaprojects with many active projects in the United States failing to meet cost and schedule efforts by significant margins. Currently, engineering teams operate in siloed tools and disparate teams where connections across design, procurement, and construction systems are translated manually or over brittle point-to-point integrations. The manual nature of data exchange increases the risk of silent errors in the reactor design, with each silent error cascading across the design. These cascading errors lead to uncontrollable risk during construction, resulting in significant delays and cost overruns. DeepLynx allows for an integrated platform during design and operations of mega projects. The DeepLynx Core API delivers a few main features. 1. Provides a set of methods and endpoints for manipulating data in an object oriented database. This allows us to store complex datatypes as records and then to compile them into actual, modifiable objects at run-time. Users can store taxonomies or ontologies in a readable format. 2. Provides methods for storing and retrieving data in a graph database. This data is structured and validated against the aformentioned object oriented database before storage.  # noqa: E501

    OpenAPI spec version: 1.0
    
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""

import pprint
import re  # noqa: F401

import six

class CreateTypeMappingTransformationsRequest(object):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    """
    Attributes:
      swagger_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    swagger_types = {
        'metatype_id': 'str',
        'conditions': 'list[TransformationCondition]',
        'keys': 'list[TransformationKey]'
    }

    attribute_map = {
        'metatype_id': 'metatype_id',
        'conditions': 'conditions',
        'keys': 'keys'
    }

    def __init__(self, metatype_id=None, conditions=None, keys=None):  # noqa: E501
        """CreateTypeMappingTransformationsRequest - a model defined in Swagger"""  # noqa: E501
        self._metatype_id = None
        self._conditions = None
        self._keys = None
        self.discriminator = None
        self.metatype_id = metatype_id
        self.conditions = conditions
        self.keys = keys

    @property
    def metatype_id(self):
        """Gets the metatype_id of this CreateTypeMappingTransformationsRequest.  # noqa: E501


        :return: The metatype_id of this CreateTypeMappingTransformationsRequest.  # noqa: E501
        :rtype: str
        """
        return self._metatype_id

    @metatype_id.setter
    def metatype_id(self, metatype_id):
        """Sets the metatype_id of this CreateTypeMappingTransformationsRequest.


        :param metatype_id: The metatype_id of this CreateTypeMappingTransformationsRequest.  # noqa: E501
        :type: str
        """
        if metatype_id is None:
            raise ValueError("Invalid value for `metatype_id`, must not be `None`")  # noqa: E501

        self._metatype_id = metatype_id

    @property
    def conditions(self):
        """Gets the conditions of this CreateTypeMappingTransformationsRequest.  # noqa: E501


        :return: The conditions of this CreateTypeMappingTransformationsRequest.  # noqa: E501
        :rtype: list[TransformationCondition]
        """
        return self._conditions

    @conditions.setter
    def conditions(self, conditions):
        """Sets the conditions of this CreateTypeMappingTransformationsRequest.


        :param conditions: The conditions of this CreateTypeMappingTransformationsRequest.  # noqa: E501
        :type: list[TransformationCondition]
        """
        if conditions is None:
            raise ValueError("Invalid value for `conditions`, must not be `None`")  # noqa: E501

        self._conditions = conditions

    @property
    def keys(self):
        """Gets the keys of this CreateTypeMappingTransformationsRequest.  # noqa: E501


        :return: The keys of this CreateTypeMappingTransformationsRequest.  # noqa: E501
        :rtype: list[TransformationKey]
        """
        return self._keys

    @keys.setter
    def keys(self, keys):
        """Sets the keys of this CreateTypeMappingTransformationsRequest.


        :param keys: The keys of this CreateTypeMappingTransformationsRequest.  # noqa: E501
        :type: list[TransformationKey]
        """
        if keys is None:
            raise ValueError("Invalid value for `keys`, must not be `None`")  # noqa: E501

        self._keys = keys

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value
        if issubclass(CreateTypeMappingTransformationsRequest, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, CreateTypeMappingTransformationsRequest):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other