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

class RSAInitRequest(object):
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
        'subject_name': 'str',
        'secur_id': 'str'
    }

    attribute_map = {
        'subject_name': 'subjectName',
        'secur_id': 'securID'
    }

    def __init__(self, subject_name=None, secur_id=None):  # noqa: E501
        """RSAInitRequest - a model defined in Swagger"""  # noqa: E501
        self._subject_name = None
        self._secur_id = None
        self.discriminator = None
        self.subject_name = subject_name
        if secur_id is not None:
            self.secur_id = secur_id

    @property
    def subject_name(self):
        """Gets the subject_name of this RSAInitRequest.  # noqa: E501


        :return: The subject_name of this RSAInitRequest.  # noqa: E501
        :rtype: str
        """
        return self._subject_name

    @subject_name.setter
    def subject_name(self, subject_name):
        """Sets the subject_name of this RSAInitRequest.


        :param subject_name: The subject_name of this RSAInitRequest.  # noqa: E501
        :type: str
        """
        if subject_name is None:
            raise ValueError("Invalid value for `subject_name`, must not be `None`")  # noqa: E501

        self._subject_name = subject_name

    @property
    def secur_id(self):
        """Gets the secur_id of this RSAInitRequest.  # noqa: E501


        :return: The secur_id of this RSAInitRequest.  # noqa: E501
        :rtype: str
        """
        return self._secur_id

    @secur_id.setter
    def secur_id(self, secur_id):
        """Sets the secur_id of this RSAInitRequest.


        :param secur_id: The secur_id of this RSAInitRequest.  # noqa: E501
        :type: str
        """

        self._secur_id = secur_id

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
        if issubclass(RSAInitRequest, dict):
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
        if not isinstance(other, RSAInitRequest):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other