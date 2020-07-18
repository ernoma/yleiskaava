
from qgis.PyQt.QtCore import QVariant

from qgis.core import (QgsProject, QgsMessageLog)


class YleiskaavaUtils:

    LAND_USE_CLASSIFICATION_ABBREVIATIONS = [
        { "plan_numbers": ["yk049"], "name": "ASUMISEN ALUE", "abbreviation": "A" },
        { "plan_numbers": ["yk049"], "name": "ASUMISEN JA VIRKISTYKSEN SEKOITTUNUT ALUE", "abbreviation": "A/V" },
        { "plan_numbers": ["yk049"], "name": "KESKUSPUISTOVERKOSTO", "abbreviation": "V" },
        { "plan_numbers": ["yk050"], "name": "VIRKISTYSALUE", "abbreviation": "V" },
        { "plan_numbers": ["yk049"], "name": "KESKUSTATOIMINTOJEN ALUE", "abbreviation": "C" },
        { "plan_numbers": ["yk049"], "name": "KESKUSTATOIMINTOJEN JA VIRKISTYKSEN SEKOITTUNUT ALUE", "abbreviation": "C/V" },
        { "plan_numbers": ["yk049"], "name": "LOMA-ASUNTOALUE", "abbreviation": "RA" },
        { "plan_numbers": ["yk049", "yk050"], "name": "LUONNONSUOJELUALUE TAI -KOHDE", "abbreviation": "SL" },
        { "plan_numbers": ["yk049"], "name": "PALVELUJEN JA TYÖPAIKKOJEN SEKOITTUNUT ALUE TAI KOHDE", "abbreviation": "P/T" },
        { "plan_numbers": ["yk049"], "name": "PUOLUSTUSVOIMIEN ALUE", "abbreviation": "EP" },
        { "plan_numbers": ["yk049"], "name": "TEOLLISUUS- JA TUOTANTOTOIMINTOJEN ALUE", "abbreviation": "T" },
        { "plan_numbers": ["yk049"], "name": "TEOLLISUUS- JA TUOTANTOTOIMINTOJEN ALUE, JOLLA YMPÄRISTÖ ASETTAA TOIMINNAN LAADULLE ERITYISIÄ VAATIMUKSIA", "abbreviation": "TY" },
        { "plan_numbers": ["yk049", "yk050"], "name": "VESIALUE", "abbreviation": "W" },
        { "plan_numbers": ["yk049"], "name": "YHTEISÖJEN LOMA-ASUNTOALUE", "abbreviation": "R" }
    ]

    def __init__(self, yleiskaavaDatabase):
        self.yleiskaavaDatabase = yleiskaavaDatabase
        

    # 
    # From Francisco Javier Carrera Arias,
    # https://www.datacamp.com/community/tutorials/fuzzy-string-python
    # (with a tiny modification)
    #
    def levenshteinRatioAndDistance(self, s, t, ratio_calc = True):
        """ levenshtein_ratio_and_distance:
            Calculates levenshtein distance between two strings.
            If ratio_calc = True, the function computes the
            levenshtein distance ratio of similarity between two strings
            For all i and j, distance[i,j] will contain the Levenshtein
            distance between the first i characters of s and the
            first j characters of t
        """
        # Initialize matrix of zeros
        rows = len(s)+1
        cols = len(t)+1

        distance = []
        for i in range(rows):
            distance.append([])
            for j in range(cols):
                distance[i].append(0)

        # Populate matrix of zeros with the indeces of each character of both strings
        for i in range(1, rows):
            for k in range(1,cols):
                distance[i][0] = i
                distance[0][k] = k

        # Iterate over the matrix to compute the cost of deletions,insertions and/or substitutions    
        for col in range(1, cols):
            for row in range(1, rows):
                if s[row-1] == t[col-1]:
                    cost = 0 # If the characters are the same in the two strings in a given position [i,j] then the cost is 0
                else:
                    # In order to align the results with those of the Python Levenshtein package, if we choose to calculate the ratio
                    # the cost of a substitution is 2. If we calculate just distance, then the cost of a substitution is 1.
                    if ratio_calc == True:
                        cost = 2
                    else:
                        cost = 1
                distance[row][col] = min(distance[row-1][col] + 1,      # Cost of deletions
                                    distance[row][col-1] + 1,          # Cost of insertions
                                    distance[row-1][col-1] + cost)     # Cost of substitutions
        if ratio_calc == True:
            # Computation of the Levenshtein Distance Ratio
            Ratio = ((len(s)+len(t)) - distance[row][col]) / (len(s)+len(t))
            return Ratio
        else:
            # print(distance) # Uncomment if you want to see the matrix showing how the algorithm computes the cost of deletions,
            # insertions and/or substitutions
            # This is the minimum number of edits needed to convert string a to string b
            return "The strings are {} edits away".format(distance[row][col])


    def getStringTypeForFeatureField(self, field):
        """ Gets the string representation of the field
        """
        if field.typeName() == 'uuid':
            return 'uuid'
        elif field.type() == QVariant.Int:
            return 'Int'
        elif field.type() == QVariant.LongLong:
            return 'LongLong'
        elif field.type() == QVariant.String:
            return 'String'
        elif field.type() == QVariant.Double:
            return 'Double'
        elif field.type() == QVariant.Date:
            return 'Date'
        if field.type() == QVariant.Bool:
            return 'Bool'
        else:
            self.iface.messageBar().pushMessage('Bugi koodissa:getStringTypeForFeatureField tuntematon tyyppi', Qgis.Critical)
            # QgsMessageLog.logMessage('getStringTypeForFeatureField tuntematon tyyppi', 'Yleiskaava-työkalu', Qgis.Critical)
            return str(field.type())


    def compatibleTypes(self, sourceFieldTypeName, targetFieldTypeName):
        if sourceFieldTypeName == targetFieldTypeName:
            return True
        elif (sourceFieldTypeName == 'Int' or sourceFieldTypeName == 'LongLong') and targetFieldTypeName == 'Double':
            return True
        elif sourceFieldTypeName == 'Bool' and (targetFieldTypeName == 'Int' or targetFieldTypeName == 'LongLong'):
            return True
        elif targetFieldTypeName == 'String':
            return True


    def getAttributeValueInCompatibleType(self, targetFieldName, targetFieldTypeName, sourceFieldTypeName, sourceAttribute):
        if targetFieldName == "id_kansallinen_prosessin_vaihe" or targetFieldName == "id_prosessin_vaihe" or targetFieldName == "id_kaavoitusprosessin_tila" or targetFieldName == "id_laillinen_sitovuus":
            return self.yleiskaavaDatabase.getCodeListUUIDForPlanObjectFieldCodeValue(targetFieldName, sourceAttribute)
        elif targetFieldTypeName == sourceFieldTypeName:
            return sourceAttribute
        else:
            if (sourceFieldTypeName == 'Int' or sourceFieldTypeName == 'LongLong') and targetFieldTypeName == 'Double':
                return sourceAttribute.toFloat()
            elif sourceFieldTypeName == 'Bool' and (targetFieldTypeName == 'Int' or targetFieldTypeName == 'LongLong'):
                return sourceAttribute.toInt()
            elif targetFieldTypeName == 'String':
                return str(sourceAttribute.value())
            else:
                self.iface.messageBar().pushMessage('Bugi koodissa: getAttributeValueInCompatibleType tuntematon tyyppimuunnos', Qgis.Critical)
                # QgsMessageLog.logMessage('getAttributeValueInCompatibleType tuntematon tyyppimuunnos', 'Yleiskaava-työkalu', Qgis.Critical)
                return None


    # def emptyGridLayout(self, gridLayout):
    #     for i in reversed(range(gridLayout.count())): 
    #         widgetToRemove = gridLayout.itemAt(i).widget()
    #         # remove it from the layout list
    #         gridLayout.removeWidget(widgetToRemove)
    #         # remove it from the gui
    #         widgetToRemove.setParent(None)


    def getLandUseClassificationNameForRegulation(self, planNumber, schemaTableName, regulationTitle):
        landUseName = regulationTitle

        if schemaTableName == 'yk_yleiskaava.kaavaobjekti_alue':
            landUseClassificationAbbrs = self.getLandUseClassificationAbbreviationsForPlan(planNumber)

            for landUseClassificationAbbr in landUseClassificationAbbrs:
                if landUseClassificationAbbr["name"] == regulationTitle:
                    landUseName = landUseClassificationAbbr["abbreviation"]
                    break

        return landUseName


    def getRegulationNameForLandUseClassification(self, planNumber, schemaTableName, landUseClassification):
        regulationName = landUseClassification

        if schemaTableName == 'yk_yleiskaava.kaavaobjekti_alue':
            landUseClassificationAbbrs = self.getLandUseClassificationAbbreviationsForPlan(planNumber)
            
            for landUseClassificationAbbr in landUseClassificationAbbrs:
                if landUseClassificationAbbr["abbreviation"] == landUseClassification:
                    regulationName = landUseClassificationAbbr["name"]
                    break

        return regulationName


    def getLandUseClassificationAbbreviationsForPlan(self, planNumber):
        landUseClassificationAbbrs = []
        
        for landUseClassificationAbbr in YleiskaavaUtils.LAND_USE_CLASSIFICATION_ABBREVIATIONS:
            if planNumber in landUseClassificationAbbr["plan_numbers"]:
                landUseClassificationAbbrs.append(landUseClassificationAbbr)

        return landUseClassificationAbbrs


    def refreshTargetLayersInProject(self):
        layerNames = self.yleiskaavaDatabase.getUserFriendlyTargetSchemaTableNames()
        for name in layerNames:
            layers = QgsProject.instance().mapLayersByName(name)
            for layer in layers:
                layer.reload()


class COPY_ERROR_REASONS:
    SELECTED_FEATURE_COUNT_IS_ZERO = 1
    TARGET_TABLE_NOT_SELECTED = 2
    TARGET_FIELD_SELECTED_MULTIPLE_TIMES = 3
