Feature: Knight Movement
  In order to win the game,
  as a player,
  I want to move my knight to empty spaces.
  Scenario Outline: Valid moves
    Given an empty chessboard
    And the <color> knight is placed on <old_x> <old_y>
    When the <color> knight tries to move to <new_x> <new_y>
    Then the <color> knight is placed at <new_x> <new_y>

  Examples:
    |color  |old_x|old_y|new_x|new_y|
    |"black"|4    |4    |3    |6    |
    |"black"|4    |4    |5    |6    |
    |"black"|4    |5    |5    |3    |
    |"black"|4    |5    |6    |4    |
    |"black"|4    |5    |6    |6    |
    |"black"|4    |5    |5    |7    |
    |"black"|4    |5    |3    |7    |
    |"black"|4    |5    |2    |6    |
    |"black"|4    |5    |2    |4    |
    |"black"|4    |5    |3    |3    |
    |"black"|1    |8    |2    |6    |
    |"black"|7    |3    |8    |1    |

  Scenario Outline: Invalid moves: wrong shape
    Given an empty chessboard
    And the <color> knight is placed on <old_x> <old_y>
    And a second <color> knight is placed on <second_x> <second_y>
    When the <color> knight tries to move to <new_x> <new_y>
    Then the <color> knight remains at <old_x> <old_y>
    And the user is told that the move failed
    Examples:
      |color  |old_x|old_y|second_x|second_y|new_x|new_y|
      |"black"|4    |4    |0       |0       |3    |7    |
      |"black"|8    |1    |2       |4       |8    |8    |
      |"black"|1    |1    |8       |8       |8    |1    |
      |"black"|2    |7    |3       |5       |7    |7    |
      |"black"|7    |2    |1       |1       |6    |2    |
      |"black"|7    |2    |1       |1       |7    |3    |
      |"black"|5    |6    |2       |2       |6    |6    |
      |"black"|5    |6    |2       |2       |8    |7    |
      |"black"|5    |5    |3       |2       |6    |9    |
      |"black"|3    |2    |1       |2       |1    |2    |
      |"black"|4    |3    |1       |5       |3    |2    |
      |"white"|4    |4    |0       |0       |3    |7    |
      |"white"|8    |1    |2       |4       |8    |8    |
      |"white"|1    |1    |8       |8       |8    |1    |
      |"white"|2    |7    |3       |5       |7    |7    |
      |"white"|7    |2    |1       |1       |6    |2    |
      |"white"|7    |2    |1       |1       |7    |3    |
      |"white"|5    |6    |2       |2       |6    |6    |
      |"white"|5    |6    |2       |2       |8    |7    |
      |"white"|5    |5    |3       |2       |6    |9    |
      |"white"|3    |2    |1       |2       |1    |2    |
      |"white"|4    |3    |1       |5       |3    |2    |


  Scenario Outline: Invalid moves: case 2 move off edge
    Given an empty chessboard
    And the <color> knight is placed on <old_x> <old_y>
    And a second <color> knight is placed on <second_x> <second_y>
    When the <color> knight tries to move to <new_x> <new_y>
    Then the <color> knight remains at <old_x> <old_y>
    And the user is told that the move failed
    Examples:
      |color  |old_x|old_y|second_x|second_y|new_x|new_y|
      |"black"|8    |0    |0       |0       |9    |2    |
      |"black"|8    |1    |2       |2       |0    |2    |
      |"black"|8    |1    |8       |8       |4    |10   |
      |"black"|1    |2    |1       |1       |8    |-1   |
      |"black"|0    |1    |0       |0       |2    |9    |
      |"white"|8    |0    |0       |0       |9    |2    |
      |"white"|8    |1    |2       |2       |0    |2    |
      |"white"|8    |1    |8       |8       |4    |10   |
      |"white"|1    |2    |1       |1       |8    |-1   |
      |"white"|0    |1    |0       |0       |2    |9    |

  Scenario Outline: Invalid moves: a move into a friendly piece
    Given an empty chessboard
    And the <color> knight is placed on <old_x> <old_y>
    And a second <color> knight is placed on <second_x> <second_y>
    When the <color> knight tries to move to <new_x> <new_y>
    Then the <color> knight remains at <old_x> <old_y>
    And the user is told that the move failed
    Examples:
      |color  |old_x|old_y|second_x|second_y|new_x|new_y|
      |"black"|1    |1    |3       |2       |3    |2    |
      |"black"|8    |1    |6       |2       |6    |2    |
      |"black"|1    |8    |2       |6       |1    |8    |
      |"black"|2    |2    |3       |4       |2    |2    |
      |"black"|7    |7    |8       |5       |8    |5    |
      |"white"|1    |1    |3       |2       |3    |2    |
      |"white"|8    |1    |6       |2       |6    |2    |
      |"white"|1    |8    |2       |6       |1    |8    |
      |"white"|2    |2    |3       |4       |2    |2    |
      |"white"|7    |7    |8       |5       |8    |5    |

  Scenario Outline: Capture Piece
    Given an empty chessboard
    And the <first_color> knight is placed on <old_x> <old_y>
    And a second <second_color> knight is placed on <second_x> <second_y>
    When the <first_color> knight tries to move to <new_x> <new_y>
    Then the <first_color> knight captures the <second_color> knight
    Examples:
      |first_color |second_color |old_x|old_y|second_x|second_y|new_x|new_y|
      |"black"|"white"|1    |1    |3       |2       |3    |2    |
      |"black"|"white"|8    |1    |6       |2       |6    |2    |
      |"black"|"white"|1    |8    |2       |6       |2    |6    |
      |"black"|"white"|2    |2    |3       |4       |3    |4    |
      |"black"|"white"|7    |7    |8       |5       |8    |5    |
      |"white"|"black"|1    |1    |3       |2       |3    |2    |
      |"white"|"black"|8    |1    |6       |2       |6    |2    |
      |"white"|"black"|1    |8    |2       |6       |2    |6    |
      |"white"|"black"|2    |2    |3       |4       |3    |4    |
      |"white"|"black"|7    |7    |8       |5       |8    |5    |