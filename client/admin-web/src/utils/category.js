function sortCategoryList(categories = []) {
  return [...categories].sort((left, right) => {
    const leftOrder = Number(left?.sort_order) || 0
    const rightOrder = Number(right?.sort_order) || 0

    if (leftOrder !== rightOrder) {
      return leftOrder - rightOrder
    }

    return String(left?.code || '').localeCompare(String(right?.code || ''), 'zh-CN')
  })
}

function buildCategoryMaps(categories = []) {
  const sortedCategories = sortCategoryList(categories)
  const categoryMap = new Map()
  const childrenMap = new Map()

  sortedCategories.forEach((category) => {
    categoryMap.set(category.code, category)
  })

  sortedCategories.forEach((category) => {
    const parentKey = category.parent_code && categoryMap.has(category.parent_code)
      ? category.parent_code
      : '__root__'

    if (!childrenMap.has(parentKey)) {
      childrenMap.set(parentKey, [])
    }

    childrenMap.get(parentKey).push(category)
  })

  return {
    sortedCategories,
    categoryMap,
    childrenMap
  }
}

function buildPathNames(category, categoryMap) {
  const names = []
  const visited = new Set()
  let current = category

  while (current && !visited.has(current.code)) {
    visited.add(current.code)
    names.unshift(current.name)

    current = current.parent_code
      ? categoryMap.get(current.parent_code)
      : null
  }

  return names
}

export function buildCategoryTree(categories = []) {
  const { categoryMap, childrenMap } = buildCategoryMaps(categories)

  function visit(parentKey = '__root__', depth = 0) {
    const list = childrenMap.get(parentKey) || []

    return list.map((category) => {
      const path_names = buildPathNames(category, categoryMap)
      const children = visit(category.code, depth + 1)

      return {
        ...category,
        depth,
        path_names,
        path_label: path_names.join(' / '),
        children,
        hasChildren: children.length > 0
      }
    })
  }

  return visit()
}

export function flattenCategoryTree(categories = []) {
  const flattened = []

  function walk(nodes = []) {
    nodes.forEach((node) => {
      flattened.push(node)

      if (node.children?.length) {
        walk(node.children)
      }
    })
  }

  walk(buildCategoryTree(categories))

  return flattened
}

export function collectDescendantCodes(categories = [], targetCode) {
  if (!targetCode) {
    return []
  }

  const { childrenMap } = buildCategoryMaps(categories)
  const descendants = []

  function walk(parentCode) {
    const children = childrenMap.get(parentCode) || []

    children.forEach((child) => {
      descendants.push(child.code)
      walk(child.code)
    })
  }

  walk(targetCode)

  return descendants
}

export function getCategoryName(categories = [], code) {
  if (!code) {
    return ''
  }

  const { categoryMap } = buildCategoryMaps(categories)

  return categoryMap.get(code)?.name || ''
}

export function getCategoryPathLabel(categories = [], code) {
  if (!code) {
    return ''
  }

  const { categoryMap } = buildCategoryMaps(categories)
  const category = categoryMap.get(code)

  if (!category) {
    return ''
  }

  return buildPathNames(category, categoryMap).join(' / ')
}

export function getRootCategories(categories = []) {
  return flattenCategoryTree(categories).filter((category) => category.depth === 0)
}

export function getChildCategories(categories = [], parentCode) {
  return flattenCategoryTree(categories).filter((category) => category.parent_code === parentCode)
}
