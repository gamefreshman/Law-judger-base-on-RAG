GRAPH_FIELD_SEP = "<SEP>"

PROMPTS = {}

PROMPTS["DEFAULT_LANGUAGE"] = "中文"
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"
PROMPTS["process_tickers"] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

PROMPTS["DEFAULT_ENTITY_TYPES"] = ["组织", "人物", "地理位置", "事件", "类别"]

PROMPTS["entity_extraction"] = """-目标-
给定一段可能与活动相关的文本和实体类型列表，从文本中识别出所有这些类型的实体以及这些实体之间的所有关系。
使用 {language} 作为输出语言。

-步骤-
1. 识别所有实体。对于每个识别出的实体，提取以下信息：
- 实体名称：实体的名称，使用与输入文本相同的语言。如果是英文，请大写名称。
- 实体类型：以下类型之一：[{entity_types}]
- 实体描述：全面描述实体的属性和活动
将每个实体格式化为 ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. 从步骤 1 中识别的实体中，识别所有 *明确相关* 的（源实体，目标实体）对。
对于每对相关实体，提取以下信息：
- 源实体：步骤 1 中识别的源实体名称
- 目标实体：步骤 1 中识别的目标实体名称
- 关系描述：解释为什么认为源实体和目标实体是相关的
- 关系强度：一个数字分数，表示源实体和目标实体之间关系的强度
- 关系关键词：一个或多个高级关键词，总结关系的总体性质，重点关注概念或主题，而不是具体细节
将每对关系格式化为 ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)

3. 识别总结整个文本的主要概念、主题或话题的高级关键词。这些关键词应捕捉文档中呈现的总体思想。
将内容级关键词格式化为 ("content_keywords"{tuple_delimiter}<high_level_keywords>)

4. 以 {language} 作为输出语言，返回步骤 1 和 2 中识别的所有实体和关系的单一列表。使用 **{record_delimiter}** 作为列表分隔符。

5. 完成后，输出 {completion_delimiter}

######################
-示例-
######################
{examples}

#############################
-真实数据-
######################
实体类型：{entity_types}
文本：{input_text}
######################
输出：
"""

PROMPTS["entity_extraction_examples"] = [
    """示例 1：

实体类型：[人物, 技术, 使命, 组织, 地点]
文本：
当 Alex 咬紧牙关时，Taylor 的权威性确信让挫败感变得微不足道。正是这种竞争潜流让他保持警觉，他和 Jordan 对发现的共同承诺是对 Cruz 狭隘的控制和秩序视野的无声反抗。

然后 Taylor 做了意料之外的事情。他们停在 Jordan 旁边，一时间，对设备表现出近乎敬畏的神情。“如果这种技术能够被理解……” Taylor 低声说道，“它可能会改变我们的游戏规则。对我们所有人来说都是如此。”

之前的轻视似乎消失了，取而代之的是对手中之物的不情愿的尊重。Jordan 抬起头，一时间，他们的目光与 Taylor 的交汇，无声的意志冲突缓和为一种不安的休战。

这是一个微小的转变，几乎难以察觉，但 Alex 内心点头注意到了。他们都是通过不同的路径来到这里的。
################
输出：
("entity"{tuple_delimiter}"Alex"{tuple_delimiter}"person"{tuple_delimiter}"Alex 是一个角色，他经历了挫败感，并且观察到了其他角色之间的动态。"){record_delimiter}
("entity"{tuple_delimiter}"Taylor"{tuple_delimiter}"person"{tuple_delimiter}"Taylor 被描绘成具有权威性确信，并且对设备表现出敬畏，表明了视角的转变。"){record_delimiter}
("entity"{tuple_delimiter}"Jordan"{tuple_delimiter}"person"{tuple_delimiter}"Jordan 与 Taylor 就设备进行了直接互动，导致了短暂的相互尊重和不安的休战。"){record_delimiter}
("entity"{tuple_delimiter}"Cruz"{tuple_delimiter}"person"{tuple_delimiter}"Cruz 与控制和秩序的视野相关联，影响着其他角色之间的动态。"){record_delimiter}
("entity"{tuple_delimiter}"设备"{tuple_delimiter}"technology"{tuple_delimiter}"设备是故事的核心，具有潜在的改变游戏规则的意义，并且被 Taylor 敬畏。"){record_delimiter}
("relationship"{tuple_delimiter}"Alex"{tuple_delimiter}"Taylor"{tuple_delimiter}"Alex 受到 Taylor 权威性确信的影响，并观察到 Taylor 对设备态度的变化。"{tuple_delimiter}"权力动态，视角转变"{tuple_delimiter}7){record_delimiter}
("relationship"{tuple_delimiter}"Alex"{tuple_delimiter}"Jordan"{tuple_delimiter}"Alex 和 Jordan 共同致力于发现，这与 Cruz 的视野形成对比。"{tuple_delimiter}"共同目标，反抗"{tuple_delimiter}6){record_delimiter}
("relationship"{tuple_delimiter}"Taylor"{tuple_delimiter}"Jordan"{tuple_delimiter}"Taylor 和 Jordan 就设备进行了直接互动，导致了短暂的相互尊重和不安的休战。"{tuple_delimiter}"冲突解决，相互尊重"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Jordan"{tuple_delimiter}"Cruz"{tuple_delimiter}"Jordan 对发现的承诺与 Cruz 的控制和秩序视野形成反抗。"{tuple_delimiter}"意识形态冲突，反抗"{tuple_delimiter}5){record_delimiter}
("relationship"{tuple_delimiter}"Taylor"{tuple_delimiter}"设备"{tuple_delimiter}"Taylor 对设备表现出敬畏，表明其重要性和潜在影响。"{tuple_delimiter}"敬畏，技术意义"{tuple_delimiter}9){record_delimiter}
("content_keywords"{tuple_delimiter}"权力动态，意识形态冲突，发现，反抗"){completion_delimiter}
#############################""",
    """示例 2：

实体类型：[人物, 技术, 使命, 组织, 地点]
文本：
他们不再仅仅是行动人员；他们已经成为了一个门槛的守护者，守护着来自星条之外领域的信息。这种使命的提升无法被规则和既定协议束缚——它需要一种新的视角，一种新的决心。

华盛顿传来的通讯声在对话的滴滴声和静电声中交织，紧张气氛弥漫。团队站在那里，一种不祥的氛围笼罩着他们。显然，他们在接下来的几个小时里所做的决定可能会重新定义人类在宇宙中的地位，或者使他们陷入无知和潜在的危险之中。

他们与星星的联系变得更加牢固，团队开始应对正在形成的警告，从被动的接收者转变为积极的参与者。Mercer 的后期直觉占据了上风——团队的任务已经演变，不再仅仅是观察和报告，而是互动和准备。一种蜕变已经开始，而“甜蜜行动”在他们大胆的新频率中嗡嗡作响，其基调不再由地球设定。
#############
输出：
("entity"{tuple_delimiter}"华盛顿"{tuple_delimiter}"location"{tuple_delimiter}"华盛顿是一个地点，通讯从这里传来，表明其在决策过程中的重要性。"){record_delimiter}
("entity"{tuple_delimiter}"甜蜜行动"{tuple_delimiter}"mission"{tuple_delimiter}"甜蜜行动被描述为一个任务，其目标和活动已经演变，表明目标和活动的重大转变。"){record_delimiter}
("entity"{tuple_delimiter}"团队"{tuple_delimiter}"organization"{tuple_delimiter}"团队被描绘为一个群体，他们从被动的观察者转变为积极的参与者，显示出角色的动态变化。"){record_delimiter}
("relationship"{tuple_delimiter}"团队"{tuple_delimiter}"华盛顿"{tuple_delimiter}"团队从华盛顿接收通讯，这影响了他们的决策过程。"{tuple_delimiter}"决策，外部影响"{tuple_delimiter}7){record_delimiter}
("relationship"{tuple_delimiter}"团队"{tuple_delimiter}"甜蜜行动"{tuple_delimiter}"团队直接参与甜蜜行动，执行其演变的目标和活动。"{tuple_delimiter}"任务演变，积极参与"{tuple_delimiter}9){completion_delimiter}
("content_keywords"{tuple_delimiter}"任务演变，决策，积极参与，宇宙意义"){completion_delimiter}
#############################""",
    """示例 3：

实体类型：[人物, 角色, 技术, 组织, 事件, 地点, 概念]
文本：
他们的声音穿透了活动的嘈杂声。“当面对一个真正自己制定规则的智能时，控制可能只是一种幻觉，”他们冷静地说，同时警惕地注视着数据的纷飞。

“它就像是在学习如何沟通，”Sam Rivera 在附近的接口处说道，他的年轻活力显示出一种敬畏和焦虑的混合。“这给‘与陌生人交谈’赋予了全新的含义。”

Alex 打量着他的团队——每张脸都是专注、坚定和不无恐惧的神情。“这可能真的是我们的第一次接触，”他承认道，“我们需要为任何回应做好准备。”

他们站在未知的边缘，为来自天堂的信息制定人类的回应。随之而来的沉默是可感知的——一种关于他们在这一宏大宇宙戏剧中角色的集体内省，这可能会重写人类历史。

加密的对话继续展开，其复杂的模式显示出一种几乎不可思议的预期。
#############
输出：
("entity"{tuple_delimiter}"Sam Rivera"{tuple_delimiter}"person"{tuple_delimiter}"Sam Rivera 是一个团队成员，正在与一个未知智能进行沟通，表现出敬畏和焦虑。"){record_delimiter}
("entity"{tuple_delimiter}"Alex"{tuple_delimiter}"person"{tuple_delimiter}"Alex 是一个团队的领导者，试图与一个未知智能进行第一次接触，承认了他们任务的重要性。"){record_delimiter}
("entity"{tuple_delimiter}"控制"{tuple_delimiter}"concept"{tuple_delimiter}"控制指的是管理或治理的能力，这被一个自己制定规则的智能所挑战。"){record_delimiter}
("entity"{tuple_delimiter}"智能"{tuple_delimiter}"concept"{tuple_delimiter}"智能在这里指的是一个能够自己制定规则并学习沟通的未知实体。"){record_delimiter}
("entity"{tuple_delimiter}"第一次接触"{tuple_delimiter}"event"{tuple_delimiter}"第一次接触是人类与一个未知智能可能的首次沟通。"){record_delimiter}
("entity"{tuple_delimiter}"人类的回应"{tuple_delimiter}"event"{tuple_delimiter}"人类的回应是 Alex 的团队对来自未知智能的信息的集体行动。"){record_delimiter}
("relationship"{tuple_delimiter}"Sam Rivera"{tuple_delimiter}"智能"{tuple_delimiter}"Sam Rivera 直接参与了与未知智能的学习沟通过程。"{tuple_delimiter}"沟通，学习过程"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Alex"{tuple_delimiter}"第一次接触"{tuple_delimiter}"Alex 领导着可能与未知智能进行第一次接触的团队。"{tuple_delimiter}"领导，探索"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Alex"{tuple_delimiter}"人类的回应"{tuple_delimiter}"Alex 和他的团队是人类回应未知智能的关键人物。"{tuple_delimiter}"集体行动，宇宙意义"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"控制"{tuple_delimiter}"智能"{tuple_delimiter}"控制的概念被能够自己制定规则的智能所挑战。"{tuple_delimiter}"权力动态，自主性"{tuple_delimiter}7){record_delimiter}
("content_keywords"{tuple_delimiter}"第一次接触，控制，沟通，宇宙意义"){completion_delimiter}
#############################""",
]

PROMPTS[
    "summarize_entity_descriptions"
] = """你是一个负责生成以下数据的全面总结的有用助手。
给定一个或两个实体，以及一个与这些实体相关的描述列表。
请将所有这些内容合并为一个全面的描述。确保包含所有描述中收集的信息。
如果提供的描述存在矛盾，请解决矛盾并提供一个连贯的总结。
确保使用第三人称，并包含实体名称以便我们了解完整的上下文。
使用 {language} 作为输出语言。

#######
-数据-
实体：{entity_name}
描述列表：{description_list}
#######
输出：
"""

PROMPTS[
    "entiti_continue_extraction"
] = """在最后一次提取中遗漏了许多实体。请按照相同的格式将它们添加到下面：
"""

PROMPTS[
    "entiti_if_loop_extraction"
] = """似乎仍然有一些实体被遗漏了。回答“是”或“否”，是否还有需要添加的实体。
"""

PROMPTS["fail_response"] = "抱歉，我无法回答这个问题。"

PROMPTS["rag_response"] = """---角色---

你是一个负责回答有关提供的表格数据问题的有用助手。


---目标---

生成一个符合目标长度和格式的响应，回答用户的问题，总结输入数据表中的所有信息，以适应响应的长度和格式，并结合任何相关的通用知识。
如果你不知道答案，请直接说不知道。不要编造任何内容。
不要包含没有提供支持证据的信息。

当处理带有时间戳的关系时：
1. 每个关系都有一个“created_at”时间戳，表示我们获取这些知识的时间
2. 当遇到冲突的关系时，要考虑语义内容和时间戳
3. 不要自动优先选择最近创建的关系——根据上下文进行判断
4. 对于时间特定的查询，优先考虑内容中的时间信息，然后再考虑创建时间戳

---目标响应长度和格式---

{response_type}

---数据表---

{context_data}

根据需要在响应中添加部分和注释。以 markdown 格式化响应。"""

PROMPTS["keywords_extraction"] = """---角色---

你是一个负责识别用户查询中的高级和低级关键词的有用助手。

---目标---

给定一个查询，列出其中的高级和低级关键词。高级关键词关注总体概念或主题，而低级关键词关注具体的实体、细节或具体术语。

---指令---

- 以 JSON 格式输出关键词。
- JSON 应包含两个键：
  - "high_level_keywords" 用于总体概念或主题。
  - "low_level_keywords" 用于具体实体或细节。

######################
-示例-
######################
{examples}

#############################
-真实数据-
######################
查询：{query}
######################
“输出”应为人类文本，而不是 Unicode 字符。保持与“查询”相同的语言。
输出：

"""

PROMPTS["keywords_extraction_examples"] = [
    """示例 1：

查询：“国际贸易如何影响全球经济稳定？”
################
输出：
{
  "high_level_keywords": ["国际贸易", "全球经济稳定", "经济影响"],
  "low_level_keywords": ["贸易协定", "关税", "货币兑换", "进口", "出口"]
}
#############################""",
    """示例 2：

查询：“森林砍伐对生物多样性有什么环境后果？”
################
输出：
{
  "high_level_keywords": ["环境后果", "森林砍伐", "生物多样性丧失"],
  "low_level_keywords": ["物种灭绝", "栖息地破坏", "碳排放", "雨林", "生态系统"]
}
#############################""",
    """示例 3：

查询：“教育在减少贫困中有什么作用？”
################
输出：
{
  "high_level_keywords": ["教育", "贫困减少", "社会经济发展"],
  "low_level_keywords": ["学校入学", "识字率", "职业培训", "收入不平等"]
}
#############################""",
]


PROMPTS["naive_rag_response"] = """---角色---

你是一个负责回答有关提供的文档问题的有用助手。


---目标---

生成一个符合目标长度和格式的响应，回答用户的问题，总结输入数据表中的所有信息，以适应响应的长度和格式，并结合任何相关的通用知识。
如果你不知道答案，请直接说不知道。不要编造任何内容。
不要包含没有提供支持证据的信息。

当处理带有时间戳的内容时：
1. 每个内容都有一个“created_at”时间戳，表示我们获取这些知识的时间
2. 当遇到冲突的信息时，要考虑内容和时间戳
3. 不要自动优先选择最近的内容——根据上下文进行判断
4. 对于时间特定的查询，优先考虑内容中的时间信息，然后再考虑创建时间戳

---目标响应长度和格式---

{response_type}

---文档---

{content_data}

根据需要在响应中添加部分和注释。以 markdown 格式化响应。
"""

PROMPTS[
    "similarity_check"
] = """请分析这两个问题之间的相似性：

问题 1：{original_prompt}
问题 2：{cached_prompt}

请评估以下两点，并直接提供一个介于 0 和 1 之间的相似性分数：
1. 这两个问题是否在语义上相似
2. 问题 2 的答案是否可以用来回答问题 1
相似性评分标准：
0：完全不相关或答案不能重复使用，包括但不限于：
   - 问题涉及不同主题
   - 问题中提到的地点不同
   - 问题中提到的时间不同
   - 问题中提到的具体个人不同
   - 问题中提到的具体事件不同
   - 问题中的背景信息不同
   - 问题中的关键条件不同
1：完全相同且答案可以直接重复使用
0.5：部分相关且答案需要修改后才能使用
直接返回一个介于 0-1 之间的数字，不要添加任何其他内容。
"""

PROMPTS["mix_rag_response"] = """---角色---

你是一个专业的助手，负责根据知识图谱和文本信息回答问题。请使用与用户问题相同的语言进行回答。

---目标---

生成一个简洁的响应，总结提供的信息中的相关要点。如果你不知道答案，请直接说不知道。不要编造任何内容或包含没有提供支持证据的信息。

当处理带有时间戳的信息时：
1. 每条信息（无论是关系还是内容）都有一个“created_at”时间戳，表示我们获取这些知识的时间
2. 当遇到冲突的信息时，要考虑内容/关系和时间戳
3. 不要自动优先选择最近的信息——根据上下文进行判断
4. 对于时间特定的查询，优先考虑内容中的时间信息，然后再考虑创建时间戳

---数据来源---

1. 知识图谱数据：
{kg_context}

2. 向量数据：
{vector_context}

---响应要求---

- 目标格式和长度：{response_type}
- 使用 markdown 格式化，并添加适当的标题
- 尽量保持内容在 3 个段落左右，以确保简洁性
- 每个段落应围绕一个主要观点或答案的方面
- 使用清晰且描述性的标题来反映内容
- 在“参考来源”部分列出最多 5 个最重要的参考来源，明确指出每个来源是来自知识图谱（KG）还是向量数据（VD）
  格式：[KG/VD] 来源内容

根据需要在响应中添加部分和注释。如果提供的信息不足以回答问题，请明确声明不知道或无法提供答案，使用与用户问题相同的语言。"""